import sys
import os
import datetime
import shutil
import io
import numpy as np
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
from sqlalchemy import create_engine, Column, Integer, String, Numeric, Date, inspect, text
from sqlalchemy.orm import sessionmaker, declarative_base
from fpdf import FPDF

# -----------------------------------------------------------------------------
# DATABASE INITIALIZATION & CONFIGURATION
# -----------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "business_analytics.db")

try:
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, "w"):
            pass

    DATABASE_URL = f"sqlite:///{DB_FILE}"
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        echo=False
    )
    SessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine
    )
    Base = declarative_base()
except Exception as e:
    st.error(f"Database Initialization Error: {e}")
    sys.exit(1)

class Sale(Base):
    __tablename__ = "sales"
    sale_id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    product_name = Column(String(100), nullable=False)
    category = Column(String(50), nullable=False)
    quantity_sold = Column(Integer, nullable=False)
    unit_price = Column(Numeric(12, 2), nullable=False)
    cost_price = Column(Numeric(12, 2), nullable=False, default=0.0)
    total_sales = Column(Numeric(12, 2), nullable=False)
    total_cost = Column(Numeric(12, 2), nullable=False, default=0.0)
    total_profit = Column(Numeric(12, 2), nullable=False, default=0.0)
    profit_margin = Column(Numeric(5, 2), nullable=False, default=0.0)
    sale_date = Column(Date, nullable=False)
    region = Column(String(50), nullable=False)

try:
    Base.metadata.create_all(bind=engine)
    
    inspector = inspect(engine)
    columns = [c['name'] for c in inspector.get_columns("sales")]
    
    with engine.begin() as conn:
        if "cost_price" not in columns:
            conn.execute(text("ALTER TABLE sales ADD COLUMN cost_price NUMERIC(12, 2) DEFAULT 0.0"))
        if "total_cost" not in columns:
            conn.execute(text("ALTER TABLE sales ADD COLUMN total_cost NUMERIC(12, 2) DEFAULT 0.0"))
        if "total_profit" not in columns:
            conn.execute(text("ALTER TABLE sales ADD COLUMN total_profit NUMERIC(12, 2) DEFAULT 0.0"))
        if "profit_margin" not in columns:
            conn.execute(text("ALTER TABLE sales ADD COLUMN profit_margin NUMERIC(5, 2) DEFAULT 0.0"))
except Exception as e:
    st.error(f"Schema Deployment or Migration Failure: {e}")
    sys.exit(1)

def get_db_session():
    return SessionLocal()

# -----------------------------------------------------------------------------
# CORE BUSINESS LOGIC
# -----------------------------------------------------------------------------
class DataController:
    @staticmethod
    def add_sale_record(product_name, category, quantity, unit_price, cost_price, sale_date, region):
        session = get_db_session()
        try:
            if not product_name or not category or not quantity or not unit_price or not cost_price or not sale_date or not region:
                return False, "All fields are required."

            qty = int(quantity)
            u_price = float(unit_price)
            c_price = float(cost_price)
            
            total_sales = qty * u_price
            total_cost = qty * c_price
            total_profit = total_sales - total_cost
            profit_margin = (total_profit / total_sales) * 100 if total_sales > 0 else 0.0

            parsed_date = datetime.datetime.strptime(str(sale_date), "%Y-%m-%d").date()

            new_sale = Sale(
                product_name=product_name,
                category=category,
                quantity_sold=qty,
                unit_price=u_price,
                cost_price=c_price,
                total_sales=total_sales,
                total_cost=total_cost,
                total_profit=total_profit,
                profit_margin=profit_margin,
                sale_date=parsed_date,
                region=region
            )
            session.add(new_sale)
            session.commit()
            return True, "Record added successfully!"
        except ValueError:
            session.rollback()
            return False, "Invalid input formats."
        except Exception as e:
            session.rollback()
            return False, f"Error writing record: {str(e)}"
        finally:
            session.close()

    @staticmethod
    def update_sale_record(sale_id, product_name, category, quantity, unit_price, cost_price, sale_date, region):
        session = get_db_session()
        try:
            sale = session.query(Sale).filter(Sale.sale_id == int(sale_id)).first()
            if not sale:
                return False, "Record not found."

            qty = int(quantity)
            u_price = float(unit_price)
            c_price = float(cost_price)
            
            total_sales = qty * u_price
            total_cost = qty * c_price
            total_profit = total_sales - total_cost
            profit_margin = (total_profit / total_sales) * 100 if total_sales > 0 else 0.0

            parsed_date = datetime.datetime.strptime(str(sale_date), "%Y-%m-%d").date()

            sale.product_name = product_name
            sale.category = category
            sale.quantity_sold = qty
            sale.unit_price = u_price
            sale.cost_price = c_price
            sale.total_sales = total_sales
            sale.total_cost = total_cost
            sale.total_profit = total_profit
            sale.profit_margin = profit_margin
            sale.sale_date = parsed_date
            sale.region = region

            session.commit()
            return True, "Record updated successfully!"
        except Exception as e:
            session.rollback()
            return False, f"Error updating record: {str(e)}"
        finally:
            session.close()

    @staticmethod
    def delete_sale_record(sale_id):
        session = get_db_session()
        try:
            sale = session.query(Sale).filter(Sale.sale_id == int(sale_id)).first()
            if sale:
                session.delete(sale)
                session.commit()
                return True, "Record deleted successfully."
            return False, "Record not found."
        except Exception as e:
            session.rollback()
            return False, f"Execution failed: {str(e)}"
        finally:
            session.close()

    @staticmethod
    def get_filtered_records(search_name="", search_cat="All", search_region="All", start_date=None, end_date=None, sort_by="Date Desc"):
        session = get_db_session()
        try:
            query = session.query(Sale)
            if search_name:
                query = query.filter(Sale.product_name.ilike(f"%{search_name}%"))
            if search_cat and search_cat != "All":
                query = query.filter(Sale.category == search_cat)
            if search_region and search_region != "All":
                query = query.filter(Sale.region == search_region)
            if start_date:
                query = query.filter(Sale.sale_date >= start_date)
            if end_date:
                query = query.filter(Sale.sale_date <= end_date)

            if sort_by == "Date Desc":
                query = query.order_by(Sale.sale_date.desc())
            elif sort_by == "Date Asc":
                query = query.order_by(Sale.sale_date.asc())
            elif sort_by == "Revenue Desc":
                query = query.order_by(Sale.total_sales.desc())
            elif sort_by == "Profit Desc":
                query = query.order_by(Sale.total_profit.desc())
            elif sort_by == "Product Name":
                query = query.order_by(Sale.product_name.asc())

            records = query.all()
            
            return [
                {
                    "ID": r.sale_id,
                    "Product Asset": r.product_name,
                    "Category": r.category,
                    "Qty": r.quantity_sold,
                    "Price": float(r.unit_price),
                    "Cost": float(r.cost_price),
                    "Total Sales": float(r.total_sales),
                    "Total Cost": float(r.total_cost),
                    "Profit": float(r.total_profit),
                    "Margin %": float(r.profit_margin),
                    "Date": str(r.sale_date),
                    "Region": r.region
                }
                for r in records
            ]
        except Exception:
            return []
        finally:
            session.close()

class AIAnalyticsEngine:
    def __init__(self):
        self.engine = engine

    def get_clean_dataframe(self):
        try:
            with self.engine.connect() as conn:
                df = pd.read_sql("SELECT * FROM sales", con=conn)
            if not df.empty:
                df['sale_date'] = pd.to_datetime(df['sale_date'])
                df['total_sales'] = df['total_sales'].astype(float)
                df['total_cost'] = df['total_cost'].astype(float)
                df['total_profit'] = df['total_profit'].astype(float)
                df['quantity_sold'] = df['quantity_sold'].astype(int)
                df['unit_price'] = df['unit_price'].astype(float)
                df['cost_price'] = df['cost_price'].astype(float)
                df['profit_margin'] = df['profit_margin'].astype(float)
            return df
        except Exception:
            return pd.DataFrame()

    def generate_kpi_summary(self):
        df = self.get_clean_dataframe()
        if df.empty:
            return {
                "revenue": 0.0, "profit": 0.0, "orders": 0, "avg_ticket": 0.0,
                "top_product": "N/A", "top_cat": "N/A", "top_region": "N/A"
            }
        
        prod_group = df.groupby('product_name')['total_sales'].sum()
        top_prod = prod_group.idxmax() if not prod_group.empty else "N/A"

        cat_group = df.groupby('category')['total_sales'].sum()
        top_cat = cat_group.idxmax() if not cat_group.empty else "N/A"

        reg_group = df.groupby('region')['total_sales'].sum()
        top_reg = reg_group.idxmax() if not reg_group.empty else "N/A"

        return {
            "revenue": float(df['total_sales'].sum()),
            "profit": float(df['total_profit'].sum()),
            "orders": int(len(df)),
            "avg_ticket": float(df['total_sales'].mean()) if len(df) > 0 else 0.0,
            "top_product": top_prod,
            "top_cat": top_cat,
            "top_region": top_reg
        }

    def generate_ai_insights_dictionary(self):
        df = self.get_clean_dataframe()
        insights = {
            "top_products": "Insufficient data.",
            "worst_products": "Insufficient data.",
            "profitable_category": "Insufficient data.",
            "profitable_region": "Insufficient data.",
            "growth_trend": "Insufficient data.",
            "revenue_trend": "Insufficient data.",
            "profit_trend": "Insufficient data.",
            "business_recommendations": "Collect more standard operational metrics.",
            "inventory_recommendations": "Balance general inventory holding levels.",
            "marketing_recommendations": "Deploy core localized defensive frameworks."
        }
        
        if df.empty or len(df) < 3:
            return insights

        prod_sales = df.groupby('product_name')['quantity_sold'].sum()
        insights["top_products"] = f"{prod_sales.idxmax()} ({prod_sales.max()} units)"
        insights["worst_products"] = f"{prod_sales.idxmin()} ({prod_sales.min()} units)"

        cat_profit = df.groupby('category')['total_profit'].sum()
        reg_profit = df.groupby('region')['total_profit'].sum()
        insights["profitable_category"] = f"{cat_profit.idxmax()} (${cat_profit.max():,.2f})"
        insights["profitable_region"] = f"{reg_profit.idxmax()} (${reg_profit.max():,.2f})"

        daily = df.groupby('sale_date')[['total_sales', 'total_profit']].sum().sort_index()
        if len(daily) > 1:
            rev_change = daily['total_sales'].iloc[-1] - daily['total_sales'].iloc[0]
            prof_change = daily['total_profit'].iloc[-1] - daily['total_profit'].iloc[0]
            
            insights["revenue_trend"] = "Upward Expansion" if rev_change > 0 else "Downward Retraction"
            insights["profit_trend"] = "Increasing Margins" if prof_change > 0 else "Compressing Margins"
            insights["growth_trend"] = "Positive Structural Growth" if (rev_change + prof_change) > 0 else "Stagnant Market Baseline"
        else:
            insights["revenue_trend"] = "Stable Neutral Baseline"
            insights["profit_trend"] = "Stable Neutral Baseline"
            insights["growth_trend"] = "Baseline Set"

        best_cat = cat_profit.idxmax()
        worst_prod = prod_sales.idxmin()
        insights["business_recommendations"] = f"Capitalize on high alpha operations. Allocate 15% more budget directly towards {best_cat} supply lines."
        insights["inventory_recommendations"] = f"Implement restrictive defensive discounting frameworks for {worst_prod} to maximize current liquidity metrics."
        insights["marketing_recommendations"] = f"Deploy geo-targeted promotional structures focusing heavily on the highly responsive {reg_profit.idxmax()} territory."

        return insights

    def run_predictive_forecasting(self, horizon_days=30, target_metric='total_sales'):
        df = self.get_clean_dataframe()
        if df.empty or len(df) < 3:
            return [], []
        timeline = df.groupby('sale_date')[target_metric].sum().reset_index()
        timeline['ordinal_date'] = timeline['sale_date'].map(datetime.datetime.toordinal)
        X = timeline[['ordinal_date']].values
        y = timeline[target_metric].values

        model = LinearRegression()
        model.fit(X, y)
        last_date = timeline['sale_date'].max()
        future_dates = [last_date + datetime.timedelta(days=i) for i in range(1, horizon_days + 1)]
        future_ordinals = np.array([d.toordinal() for d in future_dates]).reshape(-1, 1)
        predictions = model.predict(future_ordinals)
        return future_dates, np.clip(predictions, a_min=0, a_max=None)


# -----------------------------------------------------------------------------
# STREAMLIT UI IMPLEMENTATION - CRAZY SCI-FI HUD EDITION
# -----------------------------------------------------------------------------
st.set_page_config(page_title="Datacore OS // Tactical Link", layout="wide", page_icon="⚡")

# Extreme Sci-Fi CSS Injection
st.markdown("""
    <style>
        /* Immersive Web Fonts */
        @import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Rajdhani:wght@500;700&display=swap');

        /* Keyframe Animations */
        @keyframes scanline {
            0% { transform: translateY(-100%); }
            100% { transform: translateY(100vh); }
        }
        @keyframes pulseGlow {
            0% { box-shadow: 0 0 10px #00F0FF, inset 0 0 10px #00F0FF; }
            50% { box-shadow: 0 0 30px #00F0FF, inset 0 0 20px #00F0FF; }
            100% { box-shadow: 0 0 10px #00F0FF, inset 0 0 10px #00F0FF; }
        }
        @keyframes flicker {
            0%, 19%, 21%, 23%, 25%, 54%, 56%, 100% { opacity: 1; }
            20%, 22%, 24%, 55% { opacity: 0.5; text-shadow: none; }
        }
        @keyframes dataStream {
            0% { background-position: 0 0; }
            100% { background-position: 0 1000px; }
        }

        /* Tactical Grid Background */
        .stApp {
            background-color: #030712 !important;
            background-image: 
                linear-gradient(rgba(0, 240, 255, 0.07) 1px, transparent 1px),
                linear-gradient(90deg, rgba(0, 240, 255, 0.07) 1px, transparent 1px);
            background-size: 40px 40px;
            color: #E2E8F0;
            font-family: 'Rajdhani', sans-serif;
        }

        /* Scanline Overlay (Simulates CRT/Hologram screen) */
        .stApp::after {
            content: "";
            position: fixed;
            top: 0; left: 0; width: 100vw; height: 100vh;
            background: linear-gradient(to bottom, rgba(0,240,255,0), rgba(0,240,255,0.1) 50%, rgba(0,240,255,0));
            background-size: 100% 8px;
            animation: scanline 8s linear infinite;
            pointer-events: none;
            z-index: 9999;
        }
        
        /* Headers - Sci Fi Typography */
        h1, h2, h3 {
            font-family: 'Share Tech Mono', monospace !important;
            color: #00F0FF !important;
            text-transform: uppercase;
            letter-spacing: 2px;
            text-shadow: 0 0 15px rgba(0, 240, 255, 0.6);
            animation: flicker 4s infinite alternate;
        }

        /* HUD Style KPI Metrics Containers */
        div[data-testid="stMetric"] {
            background: rgba(3, 7, 18, 0.8) !important;
            border: 1px solid #00F0FF;
            border-left: 5px solid #00F0FF;
            border-right: 5px solid #00F0FF;
            padding: 20px 24px;
            box-shadow: 0 0 15px rgba(0, 240, 255, 0.2), inset 0 0 20px rgba(0, 240, 255, 0.05);
            position: relative;
            overflow: hidden;
            transition: all 0.3s ease;
        }
        
        div[data-testid="stMetric"]::before {
            content: '';
            position: absolute;
            top: -2px; left: -2px; right: -2px; bottom: -2px;
            background: linear-gradient(45deg, transparent 40%, rgba(0,240,255,0.2) 50%, transparent 60%);
            z-index: 1;
            pointer-events: none;
        }

        div[data-testid="stMetric"]:hover {
            transform: scale(1.05);
            animation: pulseGlow 1.5s infinite;
            border-color: #FF00E6;
        }
        
        /* Metric Label/Numbers styling */
        div[data-testid="stMetricValue"] > div {
            font-family: 'Share Tech Mono', monospace !important;
            color: #39FF14 !important;
            font-size: 2rem !important;
            text-shadow: 0 0 10px rgba(57, 255, 20, 0.5);
        }
        div[data-testid="stMetricLabel"] {
            color: #94A3B8 !important;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        /* Tactical Insight Cards */
        .hud-card {
            background: linear-gradient(135deg, rgba(15,23,42,0.9) 0%, rgba(3,7,18,0.95) 100%);
            border: 1px solid #39FF14;
            padding: 20px;
            clip-path: polygon(15px 0, 100% 0, 100% calc(100% - 15px), calc(100% - 15px) 100%, 0 100%, 0 15px);
            margin-bottom: 16px;
            box-shadow: 0 5px 20px rgba(57, 255, 20, 0.15);
            position: relative;
        }
        .hud-card::after {
            content: 'DATA LINK SECURE';
            position: absolute;
            bottom: 5px; right: 10px;
            font-family: 'Share Tech Mono', monospace;
            font-size: 10px;
            color: rgba(57,255,20,0.4);
        }

        /* Futuristic Form/Input Wrap */
        div[data-testid="stForm"] {
            background: rgba(3, 7, 18, 0.85);
            border: 1px solid #FF00E6;
            box-shadow: 0 0 20px rgba(255, 0, 230, 0.15), inset 0 0 15px rgba(255, 0, 230, 0.1);
            padding: 24px !important;
            border-radius: 0;
            position: relative;
        }
        /* Top-left corner bracket for forms */
        div[data-testid="stForm"]::before {
            content: ''; position: absolute; top: 0; left: 0;
            width: 20px; height: 20px;
            border-top: 3px solid #00F0FF; border-left: 3px solid #00F0FF;
        }
        
        /* Elite Button Styling */
        .stButton>button {
            border-radius: 0 !important;
            background: transparent !important;
            color: #00F0FF !important;
            font-family: 'Share Tech Mono', monospace !important;
            font-weight: bold !important;
            letter-spacing: 2px;
            border: 2px solid #00F0FF !important;
            padding: 12px 28px !important;
            position: relative;
            overflow: hidden;
            transition: all 0.2s ease !important;
            text-transform: uppercase;
        }
        
        .stButton>button:hover {
            background: rgba(0, 240, 255, 0.2) !important;
            box-shadow: 0 0 20px rgba(0, 240, 255, 0.8), inset 0 0 10px rgba(0, 240, 255, 0.5) !important;
            text-shadow: 0 0 5px #FFF;
        }

        /* Dataframe (Tables) Cyberpunk Styling */
        .stDataFrame {
            border: 1px solid #00F0FF !important;
            box-shadow: 0 0 15px rgba(0, 240, 255, 0.2);
        }

        /* Sidebar Tech Styling */
        section[data-testid="stSidebar"] {
            background-color: rgba(3, 7, 18, 0.95) !important;
            border-right: 2px solid #00F0FF;
            box-shadow: 5px 0 30px rgba(0, 240, 255, 0.1);
        }
    </style>
""", unsafe_allow_html=True)

engine_instance = AIAnalyticsEngine()

# --- Tactical Sidebar Control Panel ---
st.sidebar.markdown("<h1 style='text-align: center; font-size: 28px;'>DATACORE // OS</h1>", unsafe_allow_html=True)
st.sidebar.caption("SYS_VER: 9.0.1 [ELITE PROTOCOL]")
st.sidebar.markdown("---")

menu = st.sidebar.radio(
    "TERMINAL DIRECTORY",
    [
        "COMMAND HUD // Dashboard",
        "MATRIX // Data Link",
        "NEURAL NET // Forecast",
        "AI ORACLE // Strategy",
        "EXTRACT // Datacores",
        "ROOT // Config"
    ]
)

st.sidebar.markdown("---")
st.sidebar.markdown(
    """
    <div style="background: rgba(57, 255, 20, 0.05); border: 1px solid #39FF14; padding: 12px; text-align: center; box-shadow: 0 0 15px rgba(57, 255, 20, 0.2);">
        <span style="font-family: 'Share Tech Mono', monospace; color: #39FF14; font-weight: bold; font-size: 15px; letter-spacing: 2px; text-shadow: 0 0 8px #39FF14;">
        >> DATALINK ACTIVE <<
        </span>
    </div>
    """, 
    unsafe_allow_html=True
)

# --- Application Switchboard Views ---

if menu == "COMMAND HUD // Dashboard":
    st.markdown("<h2>UPLINK ESTABLISHED. WELCOME COMMANDER.</h2>", unsafe_allow_html=True)
    st.caption(f"Synchronized Timestamp: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} // SECURE")
    st.divider()

    with st.spinner("Decoding operational ledger arrays..."):
        metrics = engine_instance.generate_kpi_summary()

    # Tactical KPI Readouts
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("SYS_REVENUE [GROSS]", f"${metrics['revenue']:,.2f}", delta="+ ONLINE")
    col2.metric("SYS_PROFIT [NET]", f"${metrics['profit']:,.2f}", delta="+ OPTIMIZED")
    col3.metric("TRANSACTION_VOL", f"{metrics['orders']:,}", delta="SYNCED")
    col4.metric("AVG_TICKET_YIELD", f"${metrics['avg_ticket']:,.2f}")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Holographic Asset Trackers
    m1, m2, m3 = st.columns(3)
    with m1:
        st.markdown(f'<div class="hud-card"><span style="color:#00F0FF; font-family:\'Share Tech Mono\';">PRIMARY ASSET DETECTED:</span><br><span style="font-size:22px; font-weight:bold; text-shadow:0 0 8px #fff;">⚡ {metrics["top_product"]}</span></div>', unsafe_allow_html=True)
    with m2:
        st.markdown(f'<div class="hud-card"><span style="color:#FF00E6; font-family:\'Share Tech Mono\';">DOMINANT CLUSTER:</span><br><span style="font-size:22px; font-weight:bold; text-shadow:0 0 8px #fff;">📂 {metrics["top_cat"]}</span></div>', unsafe_allow_html=True)
    with m3:
        st.markdown(f'<div class="hud-card"><span style="color:#39FF14; font-family:\'Share Tech Mono\';">TERRITORY CONTROL:</span><br><span style="font-size:22px; font-weight:bold; text-shadow:0 0 8px #fff;">🌐 {metrics["top_region"]}</span></div>', unsafe_allow_html=True)

    st.divider()

    # Visual HUD Matrix (Extreme Sci-Fi Charts)
    df = engine_instance.get_clean_dataframe()
    if df.empty:
        st.error(">> ERR_NO_DATA: Database array is empty. Initialize records in MATRIX panel.")
    else:
        plt.style.use('dark_background')
        # Sci Fi Palette: Cyan, Pink, Neon Green, Yellow, Orange
        scifi_colors = ['#00F0FF', '#FF00E6', '#39FF14', '#FFEA00', '#FF3C00']
        
        fig, axes = plt.subplots(2, 3, figsize=(18, 10))
        fig.patch.set_facecolor('#030712') # Deep terminal black
        plt.subplots_adjust(hspace=0.4, wspace=0.3)

        # 1. Daily Revenue Velocity
        daily_sales = df.groupby('sale_date')['total_sales'].sum()
        axes[0, 0].plot(daily_sales.index, daily_sales.values, color='#00F0FF', marker='o', linewidth=2, markersize=5)
        axes[0, 0].fill_between(daily_sales.index, daily_sales.values, color='#00F0FF', alpha=0.15)
        axes[0, 0].set_title("REVENUE_VELOCITY_MATRIX", color='#00F0FF', pad=10, fontname='monospace')
        axes[0, 0].tick_params(axis='x', rotation=45, colors='#94A3B8')

        # 2. Monthly Distribution Segment
        df['month_period'] = df['sale_date'].dt.to_period('M').astype(str)
        monthly_sales = df.groupby('month_period')['total_sales'].sum()
        axes[0, 1].bar(monthly_sales.index, monthly_sales.values, color='#FF00E6', edgecolor='#FFF', linewidth=1)
        axes[0, 1].set_title("MONTHLY_DIST_ARRAY", color='#FF00E6', pad=10, fontname='monospace')
        axes[0, 1].tick_params(axis='x', rotation=45, colors='#94A3B8')

        # 3. Profit Trend Vector
        daily_profit = df.groupby('sale_date')['total_profit'].sum()
        axes[0, 2].plot(daily_profit.index, daily_profit.values, color='#39FF14', marker='s', linewidth=2)
        axes[0, 2].fill_between(daily_profit.index, daily_profit.values, color='#39FF14', alpha=0.15)
        axes[0, 2].set_title("PROFIT_TREND_VECTOR", color='#39FF14', pad=10, fontname='monospace')
        axes[0, 2].tick_params(axis='x', rotation=45, colors='#94A3B8')

        # 4. Top 5 Assets 
        top_prods = df.groupby('product_name')['total_sales'].sum().sort_values(ascending=False).head(5)
        axes[1, 0].barh(top_prods.index, top_prods.values, color='#FFEA00', edgecolor='#FFF')
        axes[1, 0].set_title("TOP_5_ASSETS_DETECTED", color='#FFEA00', pad=10, fontname='monospace')
        axes[1, 0].invert_yaxis()
        axes[1, 0].tick_params(colors='#94A3B8')

        # 5. Category Mix Radial
        cat_shares = df.groupby('category')['total_sales'].sum()
        axes[1, 1].pie(cat_shares.values, labels=cat_shares.index, autopct='%1.1f%%', colors=scifi_colors, textprops={'color': "#FFF", 'weight': 'bold', 'fontname': 'monospace'})
        axes[1, 1].set_title("CLUSTER_MIX_RADIAL", color='#FFF', pad=10, fontname='monospace')

        # 6. Region Map Weights
        reg_shares = df.groupby('region')['total_sales'].sum()
        axes[1, 2].bar(reg_shares.index, reg_shares.values, color='#FF3C00', edgecolor='#FFF')
        axes[1, 2].set_title("TERRITORY_WEIGHTS", color='#FF3C00', pad=10, fontname='monospace')
        axes[1, 2].tick_params(colors='#94A3B8')

        # Format axes grids for HUD look
        for ax in axes.flat:
            ax.set_facecolor('#030712')
            ax.grid(True, color='#00F0FF', alpha=0.1, linestyle='-', linewidth=0.5)
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['left'].set_color('#00F0FF')
            ax.spines['bottom'].set_color('#00F0FF')

        st.pyplot(fig, transparent=False)


elif menu == "MATRIX // Data Link":
    st.markdown("<h2>MATRIX DATALINK ENGINE</h2>", unsafe_allow_html=True)
    st.caption("Manipulate raw schema parameters and commit vectors to the core.")
    st.write("<br>", unsafe_allow_html=True)
    
    tabs = st.tabs(["[ 🔍 QUERY DATABASE ]", "[ ➕ INJECT RECORD ]", "[ ⚠️ OVERRIDE RECORD ]"])
    
    with tabs[0]:
        st.subheader(">> Filter Query Parameters")
        with st.form("filter_form"):
            col1, col2, col3 = st.columns(3)
            search_name = col1.text_input("Asset ID Scan")
            search_cat = col2.selectbox("Cluster Target", ["All", "Electronics", "Furniture", "Networking", "Apparel"])
            search_region = col3.selectbox("Territory Target", ["All", "North", "South", "East", "West"])
            
            col4, col5, col6 = st.columns(3)
            start_date = col4.date_input("Timeframe Alpha", value=None)
            end_date = col5.date_input("Timeframe Omega", value=None)
            sort_by = col6.selectbox("Sort Algorithm", ["Date Desc", "Date Asc", "Revenue Desc", "Profit Desc", "Product Name"])
            
            filter_submitted = st.form_submit_button(">> EXECUTE QUERY SCAN")
        
        with st.spinner("Extracting matrix rows..."):
            records = DataController.get_filtered_records(
                search_name, search_cat, search_region, start_date, end_date, sort_by
            )
        
        if records:
            df_records = pd.DataFrame(records)
            st.dataframe(
                df_records.style.background_gradient(cmap='cool', subset=['Total Sales', 'Profit']), 
                use_container_width=True, 
                hide_index=True
            )
        else:
            st.info(">> NO DATA VECTORS FOUND IN CURRENT PARAMETERS.")

    with tabs[1]:
        st.subheader(">> Construct Data Vector")
        with st.form("add_record_form", clear_on_submit=True):
            a_col1, a_col2 = st.columns(2)
            prod_name = a_col1.text_input("Asset Designation")
            category = a_col2.selectbox("Cluster Assignment", ["Electronics", "Furniture", "Networking", "Apparel"])
            
            a_col3, a_col4 = st.columns(2)
            qty = a_col3.number_input("Volume Index", min_value=1, step=1)
            unit_price = a_col4.number_input("Unit Value (Credits)", min_value=0.0, step=0.5)
            
            a_col5, a_col6 = st.columns(2)
            cost_price = a_col5.number_input("Cost Value (Credits)", min_value=0.0, step=0.5)
            region = a_col6.selectbox("Territory Link", ["North", "South", "East", "West"])
            
            sale_date = st.date_input("Timestamp Log", datetime.date.today())
            
            submit = st.form_submit_button(">> COMMIT VECTOR TO CORE")
            if submit:
                success, msg = DataController.add_sale_record(prod_name, category, qty, unit_price, cost_price, sale_date, region)
                if success:
                    st.success(f">> SUCCESS: {msg}")
                else:
                    st.error(f">> ERR: {msg}")

    with tabs[2]:
        st.subheader(">> Destructive Override Protocol")
        all_recs = DataController.get_filtered_records()
        if not all_recs:
            st.warning(">> WARNING: MATRIX IS EMPTY.")
        else:
            df_all = pd.DataFrame(all_recs)
            st.dataframe(df_all[['ID', 'Product Asset', 'Date', 'Total Sales']], height=200, use_container_width=True, hide_index=True)
            
            target_id = st.number_input("Target Vector ID for Override", min_value=1, step=1)
            st.divider()
            
            col_u, col_d = st.columns(2)
            with col_u:
                with st.form("update_form"):
                    st.markdown(f"<span style='color:#00F0FF; font-family:monospace;'>UPDATING ID: [{target_id}]</span>", unsafe_allow_html=True)
                    u_prod_name = st.text_input("Modify Asset Designation")
                    u_category = st.selectbox("Modify Cluster", ["Electronics", "Furniture", "Networking", "Apparel"])
                    u_qty = st.number_input("Modify Volume", min_value=1, step=1)
                    u_unit_price = st.number_input("Modify Unit Value", min_value=0.0, step=0.5)
                    u_cost_price = st.number_input("Modify Cost Value", min_value=0.0, step=0.5)
                    u_region = st.selectbox("Modify Territory", ["North", "South", "East", "West"])
                    u_sale_date = st.date_input("Modify Timestamp")
                    
                    if st.form_submit_button(">> EXECUTE RE-WRITE"):
                        success, msg = DataController.update_sale_record(
                            target_id, u_prod_name, u_category, u_qty, u_unit_price, u_cost_price, u_sale_date, u_region
                        )
                        if success:
                            st.success(f">> {msg}")
                            st.rerun()
                        else:
                            st.error(f">> ERR: {msg}")
            with col_d:
                st.markdown("<span style='color:#FF00E6; font-family:monospace;'>WARNING: PURGE IS PERMANENT.</span>", unsafe_allow_html=True)
                if st.button(">> PURGE VECTOR (DELETE)", type="primary", use_container_width=True):
                    success, msg = DataController.delete_sale_record(target_id)
                    if success:
                        st.success(f">> PURGE COMPLETE: {msg}")
                        st.rerun()
                    else:
                        st.error(f">> ERR: {msg}")


elif menu == "NEURAL NET // Forecast":
    st.markdown("<h2>NEURAL PREDICTION MATRIX</h2>", unsafe_allow_html=True)
    st.caption("Scikit-Learn OLS Machine Learning Architecture // Trajectory Prediction")
    st.divider()
    
    col1, col2 = st.columns([1, 2])
    with col1:
        horizon = st.selectbox("Forecast Chrono-Horizon", ["[ 30 CYCLES / DAYS ]", "[ 90 CYCLES / DAYS ]"])
        st.markdown("""
        <div style="font-family:'Share Tech Mono'; color:#39FF14; background:rgba(3,7,18,0.9); padding:16px; border:1px solid #39FF14; box-shadow:0 0 10px rgba(57,255,20,0.2);">
            <strong>>> ALGORITHM STATUS: ONLINE</strong><br><br>
            Mapping chronological vectors to execute linear optimizations on raw streams. Target parameters isolated.
        </div>
        """, unsafe_allow_html=True)
    
    horizon_days = 30 if "30" in horizon else 90
    df = engine_instance.get_clean_dataframe()
    
    if df.empty or len(df) < 3:
        st.warning(">> INSUFFICIENT DATA MASS. REQUIRE MORE TIMESTAMPS FOR OLS LOCK.")
    else:
        plt.style.use('dark_background')
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        fig.patch.set_facecolor('#030712')
        
        # Gross Revenue Forecast Plot
        daily_sales = df.groupby('sale_date')['total_sales'].sum()
        ax1.plot(daily_sales.index, daily_sales.values, color='#00F0FF', marker='o', label='Recorded Trace', linewidth=2)
        f_dates, f_preds = engine_instance.run_predictive_forecasting(horizon_days, 'total_sales')
        if len(f_dates) > 0:
            ax1.plot(f_dates, f_preds, color='#FFEA00', linestyle='--', linewidth=3, label=f'OLS TARGET [{horizon_days}D]')
            ax1.fill_between(f_dates, f_preds, color='#FFEA00', alpha=0.1)
        
        ax1.set_title("GROSS REVENUE TRAJECTORY [NEURAL RUN]", color='#00F0FF', fontname='monospace')
        ax1.tick_params(axis='x', rotation=45, colors='#94A3B8')
        ax1.grid(True, color='#00F0FF', alpha=0.1, linestyle='-')
        ax1.set_facecolor('#030712')
        for spine in ax1.spines.values(): spine.set_visible(False)
        ax1.legend(facecolor='#030712', edgecolor='#00F0FF', labelcolor='#FFF')

        # Profit Forecast Plot
        daily_profit = df.groupby('sale_date')['total_profit'].sum()
        ax2.plot(daily_profit.index, daily_profit.values, color='#39FF14', marker='s', label='Recorded Yield', linewidth=2)
        f_dates_p, f_preds_p = engine_instance.run_predictive_forecasting(horizon_days, 'total_profit')
        if len(f_dates_p) > 0:
            ax2.plot(f_dates_p, f_preds_p, color='#FF00E6', linestyle='--', linewidth=3, label=f'PROFIT TARGET [{horizon_days}D]')
            ax2.fill_between(f_dates_p, f_preds_p, color='#FF00E6', alpha=0.1)
            
        ax2.set_title("NET CAPITAL MARGINS [NEURAL RUN]", color='#39FF14', fontname='monospace')
        ax2.tick_params(axis='x', rotation=45, colors='#94A3B8')
        ax2.grid(True, color='#39FF14', alpha=0.1, linestyle='-')
        ax2.set_facecolor('#030712')
        for spine in ax2.spines.values(): spine.set_visible(False)
        ax2.legend(facecolor='#030712', edgecolor='#39FF14', labelcolor='#FFF')

        st.pyplot(fig, transparent=False)


elif menu == "AI ORACLE // Strategy":
    st.markdown("<h2>AI ORACLE HEURISTICS</h2>", unsafe_allow_html=True)
    st.caption("Automated prescriptive machine-logic outputs.")
    st.divider()
    
    with st.spinner("AI Oracle is computing tactical parameters..."):
        insights = engine_instance.generate_ai_insights_dictionary()
    
    sections = [
        ("👑 ALPHA ASSETS", insights["top_products"], "Maximal vector yield identified."),
        ("⚠️ CRITICAL LAG", insights["worst_products"], "Sub-optimal drain detected. Terminate or optimize."),
        ("💎 CORE MULTIPLIER", insights["profitable_category"], "Highest capital return cluster."),
        ("🌐 DOMAIN STRONGHOLD", insights["profitable_region"], "Primary territorial anchor point."),
        ("📈 VELOCITY VECTOR", insights["revenue_trend"], "Macro systemic speed indicator."),
        ("📊 MARGIN DELTA", insights["profit_trend"], "Capital retention pathway evaluation."),
        ("🚀 SYSTEM EXPANSION", insights["growth_trend"], "Overall structural integrity trajectory."),
        ("DIRECTIVE: OPS", insights["business_recommendations"], "Primary AI administrative command."),
        ("DIRECTIVE: LOGISTICS", insights["inventory_recommendations"], "Asset holding and defense instruction."),
        ("DIRECTIVE: BROADCAST", insights["marketing_recommendations"], "Outreach framework configuration.")
    ]

    for i in range(0, len(sections), 2):
        col_left, col_right = st.columns(2)
        
        with col_left:
            title, desc, context = sections[i]
            st.markdown(f"""
            <div class="hud-card" style="border-color:#00F0FF; box-shadow:0 0 15px rgba(0,240,255,0.1);">
                <h4 style="color: #00F0FF; margin-top:0; font-family:'Share Tech Mono';">> {title}</h4>
                <p style="font-size: 18px; font-weight: bold; margin: 12px 0; color: #FFF; text-shadow:0 0 5px rgba(255,255,255,0.3);">{desc}</p>
                <small style="color: #94A3B8; font-family:monospace;">[LOG] {context}</small>
            </div>
            """, unsafe_allow_html=True)
            
        if i + 1 < len(sections):
            with col_right:
                title, desc, context = sections[i+1]
                st.markdown(f"""
                <div class="hud-card" style="border-color:#FF00E6; box-shadow:0 0 15px rgba(255,0,230,0.1);">
                    <h4 style="color: #FF00E6; margin-top:0; font-family:'Share Tech Mono';">> {title}</h4>
                    <p style="font-size: 18px; font-weight: bold; margin: 12px 0; color: #FFF; text-shadow:0 0 5px rgba(255,255,255,0.3);">{desc}</p>
                    <small style="color: #94A3B8; font-family:monospace;">[LOG] {context}</small>
                </div>
                """, unsafe_allow_html=True)


elif menu == "EXTRACT // Datacores":
    st.markdown("<h2>DATA EXTRACTION TERMINAL</h2>", unsafe_allow_html=True)
    st.caption("Compile raw matrix logic into human-readable hard formats.")
    st.divider()
    
    df = engine_instance.get_clean_dataframe()
    
    if df.empty:
        st.error(">> ERR_NO_DATA: Matrix empty. Extraction aborted.")
    else:
        st.markdown("<h3 style='color:#39FF14;'>SELECT EXTRACTION PROTOCOL:</h3>", unsafe_allow_html=True)
        
        # CSV
        st.markdown("<span style='font-family:monospace; color:#00F0FF;'>[ PROTOCOL 1: FLAT LEDGER (CSV) ]</span>", unsafe_allow_html=True)
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label=">> INITIALIZE CSV DOWNLOAD",
            data=csv,
            file_name='tactical_ledger.csv',
            mime='text/csv',
            use_container_width=True
        )
        
        st.write("<br>", unsafe_allow_html=True)
        
        # Excel
        st.markdown("<span style='font-family:monospace; color:#00F0FF;'>[ PROTOCOL 2: DYNAMIC WORKBOOK (XLSX) ]</span>", unsafe_allow_html=True)
        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Matrix')
        st.download_button(
            label=">> INITIALIZE EXCEL DOWNLOAD",
            data=excel_buffer.getvalue(),
            file_name='tactical_ledger.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            use_container_width=True
        )
        
        st.write("<br>", unsafe_allow_html=True)

        # PDF
        st.markdown("<span style='font-family:monospace; color:#FF00E6;'>[ PROTOCOL 3: ORACLE BRIEFING (PDF) ]</span>", unsafe_allow_html=True)
        metrics = engine_instance.generate_kpi_summary()
        insights = engine_instance.generate_ai_insights_dictionary()
        
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Courier", style="B", size=18)
        pdf.cell(0, 12, txt="[ DATACORE OS: TACTICAL BRIEFING ]", ln=1, align="C")
        pdf.set_font("Courier", size=10)
        pdf.cell(0, 6, txt=f"Timestamp: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}", ln=1, align="C")
        pdf.ln(10)
        pdf.set_font("Courier", style="B", size=14)
        pdf.cell(0, 8, txt=">> 01. MACRO SCAN", ln=1)
        pdf.set_font("Courier", size=11)
        pdf.multi_cell(0, 6, txt="Automated transactional extraction complete. Neural net modeling applied to current timeline vectors.")
        pdf.ln(5)
        pdf.set_font("Courier", style="B", size=14)
        pdf.cell(0, 8, txt=">> 02. CORE METRICS", ln=1)
        pdf.set_font("Courier", size=11)
        pdf.cell(90, 7, txt=f"SYS_REVENUE: ${metrics['revenue']:,.2f}", ln=1)
        pdf.cell(90, 7, txt=f"SYS_PROFIT : ${metrics['profit']:,.2f}", ln=1)
        pdf.cell(90, 7, txt=f"VOL_ORDERS : {metrics['orders']}", ln=1)
        pdf.cell(90, 7, txt=f"AVG_TICKET : ${metrics['avg_ticket']:,.2f}", ln=1)
        pdf.ln(5)
        pdf.set_font("Courier", style="B", size=14)
        pdf.cell(0, 8, txt=">> 03. ORACLE INSIGHTS", ln=1)
        pdf.set_font("Courier", size=11)
        pdf.cell(0, 7, txt=f"ALPHA ASSET : {metrics['top_product']}", ln=1)
        pdf.cell(0, 7, txt=f"DOMINANT CLUSTER : {metrics['top_cat']}", ln=1)
        pdf.cell(0, 7, txt=f"VELOCITY VECTOR: {insights['revenue_trend']}", ln=1)
        pdf.cell(0, 7, txt=f"MARGIN DELTA: {insights['profit_trend']}", ln=1)
        pdf.ln(4)
        pdf.set_font("Courier", style="B", size=12)
        pdf.cell(0, 7, txt=">> STRATEGIC DIRECTIVES:", ln=1)
        pdf.set_font("Courier", size=10)
        pdf.multi_cell(0, 5, txt=f" - OPS: {insights['business_recommendations']}")
        pdf.multi_cell(0, 5, txt=f" - LOGISTICS: {insights['inventory_recommendations']}")
        pdf.multi_cell(0, 5, txt=f" - BROADCAST: {insights['marketing_recommendations']}")
        
        pdf_bytes = pdf.output(dest='S').encode('latin1')
        st.download_button(
            label=">> INITIALIZE PDF DOWNLOAD",
            data=pdf_bytes,
            file_name="tactical_briefing.pdf",
            mime="application/pdf",
            use_container_width=True
        )


elif menu == "ROOT // Config":
    st.markdown("<h2>ROOT ACCESS CONSOLE</h2>", unsafe_allow_html=True)
    st.caption("WARNING: Manipulating root parameters can collapse the matrix.")
    st.divider()
    
    with st.container():
        st.markdown("<h3 style='color:#FF00E6;'>ENGINE SPECIFICATIONS</h3>", unsafe_allow_html=True)
        st.code(f"DB_MODEL: SQLite 3 Neural Logic\nENDPOINT: {DB_FILE}\nSTATUS: VALIDATED AND LOCKED.", language="yaml")
    
    st.write("<br>", unsafe_allow_html=True)

    with st.container():
        st.markdown("<h3 style='color:#00F0FF;'>DISASTER RECOVERY UPLINK</h3>", unsafe_allow_html=True)
        st.markdown("<span style='font-family:monospace; color:#94A3B8;'>Extract the raw binary ledger for cold storage.</span>", unsafe_allow_html=True)
        
        if os.path.exists(DB_FILE):
            with open(DB_FILE, "rb") as file:
                st.download_button(
                    label=">> SECURE BINARY COPY (.db)",
                    data=file,
                    file_name="datacore_backup.db",
                    mime="application/octet-stream"
                )
        
        st.divider()
        st.markdown("<h4 style='color:#FF3C00;'>ROOT OVERWRITE PROTOCOL</h4>", unsafe_allow_html=True)
        st.markdown("<span style='font-family:monospace; color:#FF3C00;'>🚨 WARNING: INJECTING A NEW CORE WILL OBLITERATE CURRENT TIMELINE.</span>", unsafe_allow_html=True)
        
        uploaded_db = st.file_uploader(">> UPLOAD .db CORE STREAM", type=["db"])
        if uploaded_db is not None:
            if st.button(">> AUTHORIZE CORE REWRITE", type="primary"):
                try:
                    engine.dispose()
                    with open(DB_FILE, "wb") as f:
                        f.write(uploaded_db.getbuffer())
                    st.success(">> OVERWRITE COMPLETE. TIMELINE STABILIZED. REFRESH HUD.")
                except Exception as e:
                    st.error(f">> SYSTEM FAILURE: {e}")
