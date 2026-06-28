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
# CORE BUSINESS LOGIC (CONTROLLERS & ENGINES)
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
# STREAMLIT UI IMPLEMENTATION
# -----------------------------------------------------------------------------
st.set_page_config(page_title="Datacore Pro // Enterprise Analytics", layout="wide", page_icon="📈")

# Premium Custom CSS Injection for Glassmorphic Dark UI and Smooth Interactions
st.markdown("""
    <style>
        /* Base Background Canvas Gradient */
        .stApp {
            background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%);
            color: #E2E8F0;
        }
        
        /* Modern Glassmorphic Cards Container styling */
        div[data-testid="stMetric"] {
            background: rgba(30, 41, 59, 0.45);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 16px;
            padding: 20px 24px;
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.2);
            transition: transform 0.25s ease, border-color 0.25s ease;
        }
        div[data-testid="stMetric"]:hover {
            transform: translateY(-4px);
            border-color: rgba(99, 102, 241, 0.4);
        }
        
        /* Custom Info/Highlight Callouts */
        .custom-card {
            background: rgba(30, 41, 59, 0.6);
            border-left: 5px solid #6366F1;
            padding: 16px;
            border-radius: 8px;
            margin-bottom: 12px;
        }
        
        /* Form, Input Fields & Dropdowns custom wrapping */
        div[data-testid="stForm"] {
            background: rgba(15, 23, 42, 0.6);
            border-radius: 16px;
            border: 1px solid rgba(255, 255, 255, 0.05);
            padding: 24px !important;
        }
        
        /* Button Transitions and Premium Effects */
        .stButton>button {
            border-radius: 10px !important;
            background: linear-gradient(90deg, #4F46E5 0%, #6366F1 100%) !important;
            color: white !important;
            font-weight: 600 !important;
            border: none !important;
            padding: 10px 24px !important;
            box-shadow: 0 4px 14px 0 rgba(79, 70, 229, 0.4) !important;
            transition: all 0.3s ease-in-out !important;
        }
        .stButton>button:hover {
            transform: scale(1.02);
            box-shadow: 0 6px 20px 0 rgba(99, 102, 241, 0.6) !important;
        }
        
        /* Secondary Action Buttons (e.g., Download, Primary Destructive) */
        div[data-testid="stDownloadButton"]>button {
            border-radius: 10px !important;
            background: rgba(51, 65, 85, 0.6) !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            color: #F8FAFC !important;
            transition: all 0.25s ease !important;
        }
        div[data-testid="stDownloadButton"]>button:hover {
            background: rgba(71, 85, 105, 0.8) !important;
            border-color: #6366F1 !important;
        }
        
        /* Sidebar Styling Fixes */
        section[data-testid="stSidebar"] {
            background-color: #0B0F19 !important;
            border-right: 1px solid rgba(255, 255, 255, 0.05);
        }
    </style>
""", unsafe_allow_html=True)

engine_instance = AIAnalyticsEngine()

# --- Sidebar Navigation Control ---
st.sidebar.title("DATACORE // PRO AI")
st.sidebar.caption("Enterprise Control Dock v3.5")
st.sidebar.markdown("---")

menu = st.sidebar.radio(
    "Navigation Menu",
    [
        "📊 Executive Dashboard",
        "📝 Data Management",
        "🔮 Predictive ML Models",
        "🤖 AI Strategic Analysis",
        "📁 Reports & File Exports",
        "⚙️ System Settings"
    ]
)

st.sidebar.markdown("---")
st.sidebar.markdown(
    """
    <div style="background: rgba(16, 185, 129, 0.1); border: 1px solid #10B981; border-radius: 8px; padding: 10px; text-align: center;">
        <span style="color: #10B981; font-weight: bold; font-size: 13px;">🟢 SYSTEM ENG ACTIVE</span>
    </div>
    """, 
    unsafe_allow_html=True
)

# --- Application Switchboard Views ---

if menu == "📊 Executive Dashboard":
    st.title("Welcome Back, Administrator 👋")
    st.caption(f"Sales Analytics Control Center • Last Updated: {datetime.datetime.now().strftime('%A, %B %d, %Y')}")
    st.divider()

    with st.spinner("Processing live operational ledger..."):
        metrics = engine_instance.generate_kpi_summary()

    # Premium KPI Cards Row
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Gross Revenue", f"${metrics['revenue']:,.2f}", delta="Yield Metrics")
    col2.metric("Operational Profit", f"${metrics['profit']:,.2f}", delta="Net Margins")
    col3.metric("Volumetric Orders", f"{metrics['orders']:,}", delta="Transactions")
    col4.metric("Average Ticket Value", f"${metrics['avg_ticket']:,.2f}")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Context Asset Badges using Styled Containers
    m1, m2, m3 = st.columns(3)
    with m1:
        st.markdown(f'<div class="custom-card"><strong>Alpha Product Asset:</strong><br>🏆 {metrics["top_product"]}</div>', unsafe_allow_html=True)
    with m2:
        st.markdown(f'<div class="custom-card"><strong>Top Segment Category:</strong><br>📁 {metrics["top_cat"]}</div>', unsafe_allow_html=True)
    with m3:
        st.markdown(f'<div class="custom-card"><strong>Dominant Sales Region:</strong><br>🌎 {metrics["top_region"]}</div>', unsafe_allow_html=True)

    st.divider()

    # Visual Matrix Section
    df = engine_instance.get_clean_dataframe()
    if df.empty:
        st.warning("No enterprise records initialized yet. Please populate database variables in the Data Management tab.")
    else:
        # Dark style palette configurations for Matplotlib matching dashboard theme
        plt.style.use('dark_background')
        fig, axes = plt.subplots(2, 3, figsize=(18, 10))
        fig.patch.set_facecolor('#0F172A')
        plt.subplots_adjust(hspace=0.4, wspace=0.3)

        # 1. Daily Revenue
        daily_sales = df.groupby('sale_date')['total_sales'].sum()
        axes[0, 0].plot(daily_sales.index, daily_sales.values, color='#6366F1', marker='o', linewidth=2)
        axes[0, 0].set_title("Daily Revenue Velocity", color='#E2E8F0', pad=10)
        axes[0, 0].tick_params(axis='x', rotation=45, colors='#94A3B8')
        axes[0, 0].set_facecolor('#1E293B')

        # 2. Monthly Sales
        df['month_period'] = df['sale_date'].dt.to_period('M').astype(str)
        monthly_sales = df.groupby('month_period')['total_sales'].sum()
        axes[0, 1].bar(monthly_sales.index, monthly_sales.values, color='#3B82F6')
        axes[0, 1].set_title("Monthly Sales Distribution", color='#E2E8F0', pad=10)
        axes[0, 1].tick_params(axis='x', rotation=45, colors='#94A3B8')
        axes[0, 1].set_facecolor('#1E293B')

        # 3. Net Capital Profit Trend
        daily_profit = df.groupby('sale_date')['total_profit'].sum()
        axes[0, 2].plot(daily_profit.index, daily_profit.values, color='#10B981', marker='s', linewidth=2)
        axes[0, 2].set_title("Net Capital Profit Trend", color='#E2E8F0', pad=10)
        axes[0, 2].tick_params(axis='x', rotation=45, colors='#94A3B8')
        axes[0, 2].set_facecolor('#1E293B')

        # 4. Top 5 Products
        top_prods = df.groupby('product_name')['total_sales'].sum().sort_values(ascending=False).head(5)
        axes[1, 0].barh(top_prods.index, top_prods.values, color='#8B5CF6')
        axes[1, 0].set_title("Top 5 Product Assets", color='#E2E8F0', pad=10)
        axes[1, 0].invert_yaxis()
        axes[1, 0].tick_params(colors='#94A3B8')
        axes[1, 0].set_facecolor('#1E293B')

        # 5. Category Mix
        cat_shares = df.groupby('category')['total_sales'].sum()
        axes[1, 1].pie(cat_shares.values, labels=cat_shares.index, autopct='%1.1f%%', colors=['#6366F1', '#10B981', '#8B5CF6', '#F59E0B', '#EC4899'], textprops={'color': "#E2E8F0"})
        axes[1, 1].set_title("Categorical Mix Matrix", color='#E2E8F0', pad=10)
        axes[1, 1].set_facecolor('#1E293B')

        # 6. Regional Weights
        reg_shares = df.groupby('region')['total_sales'].sum()
        axes[1, 2].bar(reg_shares.index, reg_shares.values, color='#06B6D4')
        axes[1, 2].set_title("Regional Revenue Weights", color='#E2E8F0', pad=10)
        axes[1, 2].tick_params(colors='#94A3B8')
        axes[1, 2].set_facecolor('#1E293B')

        # Format axes grids
        for ax in axes.flat:
            ax.grid(True, alpha=0.15, linestyle=':')
            ax.spines['top'].set_visible(false) if hasattr(ax, 'spines') else None
            ax.spines['right'].set_visible(false) if hasattr(ax, 'spines') else None

        st.pyplot(fig)


elif menu == "📝 Data Management":
    st.title("Data Management Engine")
    st.caption("Inspect pipeline variables, add transactional assets, or adjust current schema records.")
    st.write("<br>", unsafe_allow_html=True)
    
    tabs = st.tabs(["🔍 View & Filter Database", "➕ Add New Record", "🔄 Modify Existing Record"])
    
    with tabs[0]:
        st.subheader("Filter Matrix Parameters")
        with st.form("filter_form"):
            col1, col2, col3 = st.columns(3)
            search_name = col1.text_input("Search Product Asset")
            search_cat = col2.selectbox("Category Dropdown", ["All", "Electronics", "Furniture", "Networking", "Apparel"])
            search_region = col3.selectbox("Region Dropdown", ["All", "North", "South", "East", "West"])
            
            col4, col5, col6 = st.columns(3)
            start_date = col4.date_input("Start Date Filter", value=None)
            end_date = col5.date_input("End Date Filter", value=None)
            sort_by = col6.selectbox("Sort Engine Priority", ["Date Desc", "Date Asc", "Revenue Desc", "Profit Desc", "Product Name"])
            
            filter_submitted = st.form_submit_button("🔄 Refresh Data Matrix")
        
        with st.spinner("Fetching active records..."):
            records = DataController.get_filtered_records(
                search_name, search_cat, search_region, start_date, end_date, sort_by
            )
        
        if records:
            df_records = pd.DataFrame(records)
            st.dataframe(
                df_records.style.background_gradient(cmap='Blues', subset=['Total Sales', 'Profit']), 
                use_container_width=True, 
                hide_index=True
            )
        else:
            st.info("No records match the current filter parameters.")

    with tabs[1]:
        st.subheader("Commit New Entry Vector")
        with st.form("add_record_form", clear_on_submit=True):
            a_col1, a_col2 = st.columns(2)
            prod_name = a_col1.text_input("Product Name Identifier")
            category = a_col2.selectbox("Operational Category Segment", ["Electronics", "Furniture", "Networking", "Apparel"])
            
            a_col3, a_col4 = st.columns(2)
            qty = a_col3.number_input("Quantity Volumetric Component", min_value=1, step=1)
            unit_price = a_col4.number_input("Unit Price Baseline ($)", min_value=0.0, step=0.5)
            
            a_col5, a_col6 = st.columns(2)
            cost_price = a_col5.number_input("Cost Price Target ($)", min_value=0.0, step=0.5)
            region = a_col6.selectbox("Target Regional Territory", ["North", "South", "East", "West"])
            
            sale_date = st.date_input("Sale Verification Date", datetime.date.today())
            
            submit = st.form_submit_button("➕ Commit Entry to System")
            if submit:
                success, msg = DataController.add_sale_record(prod_name, category, qty, unit_price, cost_price, sale_date, region)
                if success:
                    st.success(msg)
                else:
                    st.error(msg)

    with tabs[2]:
        st.subheader("Update or Drop Structural Record")
        all_recs = DataController.get_filtered_records()
        if not all_recs:
            st.warning("No records exist in the system architecture currently.")
        else:
            df_all = pd.DataFrame(all_recs)
            st.dataframe(df_all[['ID', 'Product Asset', 'Date', 'Total Sales']], height=200, use_container_width=True, hide_index=True)
            
            target_id = st.number_input("Target Record ID Sequence to Modify/Delete", min_value=1, step=1)
            st.divider()
            
            col_u, col_d = st.columns(2)
            with col_u:
                with st.form("update_form"):
                    st.markdown(f"#### Update Values for ID: **{target_id}**")
                    u_prod_name = st.text_input("New Product Name Input")
                    u_category = st.selectbox("New Category Assignment", ["Electronics", "Furniture", "Networking", "Apparel"])
                    u_qty = st.number_input("New Quantity Volume", min_value=1, step=1)
                    u_unit_price = st.number_input("New Unit Price Index ($)", min_value=0.0, step=0.5)
                    u_cost_price = st.number_input("New Cost Price Index ($)", min_value=0.0, step=0.5)
                    u_region = st.selectbox("New Target Region Domain", ["North", "South", "East", "West"])
                    u_sale_date = st.date_input("New Timestamp Vector")
                    
                    if st.form_submit_button("🔄 Update Specified Record"):
                        success, msg = DataController.update_sale_record(
                            target_id, u_prod_name, u_category, u_qty, u_unit_price, u_cost_price, u_sale_date, u_region
                        )
                        if success:
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)
            with col_d:
                st.markdown("#### Destructive Actions Zone")
                st.info("Dropping database records is permanent and will rewrite structural OLS modeling parameters.")
                if st.button("🗑️ Drop Record Permanently (Delete)", type="primary", use_container_width=True):
                    success, msg = DataController.delete_sale_record(target_id)
                    if success:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)


elif menu == "🔮 Predictive ML Models":
    st.title("Horizon Target Forecasting Configuration")
    st.caption("Scikit-Learn Ordinary Least Squares (OLS) Linear Regression Processing Matrix.")
    st.divider()
    
    col1, col2 = st.columns([1, 2])
    with col1:
        horizon = st.selectbox("Forecast Horizon Interval Selection", ["30 Days Target", "90 Days Extended Target"])
        st.markdown("""
        <div style="font-size: 13px; color:#94A3B8; background:rgba(255,255,255,0.02); padding:12px; border-radius:8px; border:1px solid rgba(255,255,255,0.05)">
            <strong>Engine Specifications:</strong><br>
            Maps timeline vectors using chronological ordinals to execute linear trajectory optimizations on operational data streams.
        </div>
        """, unsafe_allow_html=True)
    
    horizon_days = 30 if "30" in horizon else 90
    df = engine_instance.get_clean_dataframe()
    
    if df.empty or len(df) < 3:
        st.warning("Insufficient vector density. Please supply more historical date metrics to generate models.")
    else:
        plt.style.use('dark_background')
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        fig.patch.set_facecolor('#0F172A')
        
        # Gross Revenue Forecast Plot
        daily_sales = df.groupby('sale_date')['total_sales'].sum()
        ax1.plot(daily_sales.index, daily_sales.values, color='#3B82F6', marker='o', label='Historical Track', linewidth=2)
        f_dates, f_preds = engine_instance.run_predictive_forecasting(horizon_days, 'total_sales')
        if len(f_dates) > 0:
            ax1.plot(f_dates, f_preds, color='#F59E0B', linestyle='--', linewidth=2, label=f'OLS Projection ({horizon_days}D)')
        ax1.set_title("Gross Revenue Trajectory Forecast Model", color='#E2E8F0')
        ax1.tick_params(axis='x', rotation=45, colors='#94A3B8')
        ax1.grid(True, alpha=0.15)
        ax1.set_facecolor('#1E293B')
        ax1.legend()

        # Profit Forecast Plot
        daily_profit = df.groupby('sale_date')['total_profit'].sum()
        ax2.plot(daily_profit.index, daily_profit.values, color='#10B981', marker='s', label='Historical Net Yield', linewidth=2)
        f_dates_p, f_preds_p = engine_instance.run_predictive_forecasting(horizon_days, 'total_profit')
        if len(f_dates_p) > 0:
            ax2.plot(f_dates_p, f_preds_p, color='#EF4444', linestyle='--', linewidth=2, label=f'Profit Model Target ({horizon_days}D)')
        ax2.set_title("Net Capital Margins Structural Forecast", color='#E2E8F0')
        ax2.tick_params(axis='x', rotation=45, colors='#94A3B8')
        ax2.grid(True, alpha=0.15)
        ax2.set_facecolor('#1E293B')
        ax2.legend()

        st.pyplot(fig)


elif menu == "🤖 AI Strategic Analysis":
    st.title("AI Enterprise Strategic Core Engine")
    st.caption("Automated prescriptive summaries and transactional alpha analytics models.")
    st.divider()
    
    with st.spinner("Compiling automated strategic heuristics..."):
        insights = engine_instance.generate_ai_insights_dictionary()
    
    sections = [
        ("🏆 Top Performing Corporate Assets", insights["top_products"], "Maximum volume metrics output vector."),
        ("📉 Lagging Operational Matrix Segments", insights["worst_products"], "Sub-optimal optimization baseline target."),
        ("💎 Profit Maximization Core Units", insights["profitable_category"], "Highest alpha return structural channel."),
        ("🗺️ Core Geographical Domain Stronghold", insights["profitable_region"], "Dominant territory conversion density."),
        ("📈 Systemic Revenue Trend Matrix Velocity", insights["revenue_trend"], "Gross transaction speed indicator."),
        ("📊 Systemic Capital Profit Margin Track", insights["profit_trend"], "Delta margin evaluation path."),
        ("🚀 Composite System Expansion Metrics", insights["growth_trend"], "General industrial strength evaluation framework."),
        ("💡 Strategic Corporate Business Execution Directive", insights["business_recommendations"], "Prescriptive administrative operations trajectory."),
        ("📦 Logistical Inventory Asset Optimization Allocation", insights["inventory_recommendations"], "Supply stream defensive holding instructions."),
        ("📣 Promotional Outreach Targeted Deployment Matrix", insights["marketing_recommendations"], "Geo-targeted public scaling framework configuration.")
    ]

    # Grid Display for Insights Matrix
    for i in range(0, len(sections), 2):
        col_left, col_right = st.columns(2)
        
        with col_left:
            title, desc, context = sections[i]
            st.markdown(f"""
            <div style="background: rgba(30, 41, 59, 0.45); border: 1px solid rgba(255,255,255,0.06); padding: 20px; border-radius: 12px; margin-bottom: 20px;">
                <h4 style="color: #6366F1; margin-top:0;">{title}</h4>
                <p style="font-size: 16px; font-weight: bold; margin: 8px 0; color: #F8FAFC;">{desc}</p>
                <small style="color: #64748B;">Context: {context}</small>
            </div>
            """, unsafe_allow_html=True)
            
        if i + 1 < len(sections):
            with col_right:
                title, desc, context = sections[i+1]
                st.markdown(f"""
                <div style="background: rgba(30, 41, 59, 0.45); border: 1px solid rgba(255,255,255,0.06); padding: 20px; border-radius: 12px; margin-bottom: 20px;">
                    <h4 style="color: #10B981; margin-top:0;">{title}</h4>
                    <p style="font-size: 16px; font-weight: bold; margin: 8px 0; color: #F8FAFC;">{desc}</p>
                    <small style="color: #64748B;">Context: {context}</small>
                </div>
                """, unsafe_allow_html=True)


elif menu == "📁 Reports & File Exports":
    st.title("Enterprise Financial Data Export Center")
    st.caption("Compile system variables into automated downstream ledgers and summaries.")
    st.divider()
    
    df = engine_instance.get_clean_dataframe()
    
    if df.empty:
        st.warning("There is no structural data to export yet.")
    else:
        st.markdown("### Select Target Export Channel:")
        
        # CSV Export Card Block
        st.markdown("#### 📄 Flat Ledger Formats")
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Export Core Ledger to Flat File (CSV)",
            data=csv,
            file_name='enterprise_ledger.csv',
            mime='text/csv',
            use_container_width=True
        )
        
        st.write("<br>", unsafe_allow_html=True)
        
        # Excel Export Card Block
        st.markdown("#### 📈 Dynamic Workbook Sheets")
        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Ledger')
        st.download_button(
            label="Compile Operational Sheet Workbooks (XLSX)",
            data=excel_buffer.getvalue(),
            file_name='enterprise_ledger.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            use_container_width=True
        )
        
        st.write("<br>", unsafe_allow_html=True)

        # PDF Compilation Card Block
        st.markdown("#### 👑 High-Executive Summary Documents")
        metrics = engine_instance.generate_kpi_summary()
        insights = engine_instance.generate_ai_insights_dictionary()
        
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Helvetica", style="B", size=18)
        pdf.cell(0, 12, txt="Enterprise Data Analytics & Predictive Forecast Report", ln=1, align="C")
        pdf.set_font("Helvetica", size=10)
        pdf.cell(0, 6, txt=f"Generated Date Engine Sequence: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}", ln=1, align="C")
        pdf.ln(10)
        pdf.set_font("Helvetica", style="B", size=14)
        pdf.cell(0, 8, txt="1. Corporate Operations Overview", ln=1)
        pdf.set_font("Helvetica", size=11)
        pdf.multi_cell(0, 6, txt="This analytical executive summary encompasses automated transactional operational pipelines, parsing live margins, asset velocities, and linear machine learning future targets.")
        pdf.ln(5)
        pdf.set_font("Helvetica", style="B", size=14)
        pdf.cell(0, 8, txt="2. Core Financial KPI Summary Matrix", ln=1)
        pdf.set_font("Helvetica", size=11)
        pdf.cell(90, 7, txt=f"Total Gross Revenue: ${metrics['revenue']:,.2f}", ln=1)
        pdf.cell(90, 7, txt=f"Total Net Capital Profit: ${metrics['profit']:,.2f}", ln=1)
        pdf.cell(90, 7, txt=f"Total Processed Volume Orders: {metrics['orders']}", ln=1)
        pdf.cell(90, 7, txt=f"Average Order Ticket Value: ${metrics['avg_ticket']:,.2f}", ln=1)
        pdf.ln(5)
        pdf.set_font("Helvetica", style="B", size=14)
        pdf.cell(0, 8, txt="3. Structural Margin Analytics & AI Insights", ln=1)
        pdf.set_font("Helvetica", size=11)
        pdf.cell(0, 7, txt=f"Alpha Product Asset: {metrics['top_product']}", ln=1)
        pdf.cell(0, 7, txt=f"Dominant Structural Segment Category: {metrics['top_cat']}", ln=1)
        pdf.cell(0, 7, txt=f"Revenue Horizon State: {insights['revenue_trend']}", ln=1)
        pdf.cell(0, 7, txt=f"Profit Horizon State: {insights['profit_trend']}", ln=1)
        pdf.ln(4)
        pdf.set_font("Helvetica", style="B", size=12)
        pdf.cell(0, 7, txt="Corporate Strategy Action Items:", ln=1)
        pdf.set_font("Helvetica", size=10)
        pdf.multi_cell(0, 5, txt=f"- Executive Recommendation: {insights['business_recommendations']}")
        pdf.multi_cell(0, 5, txt=f"- Logistics Framework: {insights['inventory_recommendations']}")
        pdf.multi_cell(0, 5, txt=f"- Outreach Allocation: {insights['marketing_recommendations']}")
        
        pdf_bytes = pdf.output(dest='S').encode('latin1')
        st.download_button(
            label="Generate AI Executive Core Document (PDF)",
            data=pdf_bytes,
            file_name="executive_summary.pdf",
            mime="application/pdf",
            use_container_width=True
        )


elif menu == "⚙️ System Settings":
    st.title("Infrastructure Controls & Preferences")
    st.caption("Manage back-end schema specifications and database rollback systems.")
    st.divider()
    
    with st.container():
        st.subheader("Visual Presentation Theme")
        st.info("Theme presentation frameworks (Dark/Light Canvas variants) are natively handled by Streamlit. Customize layouts directly inside Settings -> Theme panels.")

    st.write("<br>", unsafe_allow_html=True)

    with st.container():
        st.subheader("Data Core Architecture Specifications Matrix")
        st.code(f"Database Model Form: SQLite 3 relational local engine\nTarget Active Endpoint Mapping: {DB_FILE}\nTable Validation Index: Schema definitions verified.", language="yaml")
    
    st.write("<br>", unsafe_allow_html=True)

    with st.container():
        st.subheader("Administrative Disaster Recovery & Backup Pipelines")
        st.markdown("Ensure state preservation by downloading a direct physical backup copy of the SQLite runtime binary ledger.")
        
        if os.path.exists(DB_FILE):
            with open(DB_FILE, "rb") as file:
                st.download_button(
                    label="💾 Download Raw Core Database Ledger (.db)",
                    data=file,
                    file_name="business_analytics_backup.db",
                    mime="application/octet-stream"
                )
        
        st.divider()
        st.markdown("#### Database Overwrite (Restore Pipeline)")
        st.warning("🚨 WARNING: Uploading a configuration file here completely rewrites and overwrites current data mappings.")
        
        uploaded_db = st.file_uploader("Upload .db Backup File Stream", type=["db"])
        if uploaded_db is not None:
            if st.button("🚨 Confirm Core Overwrite Sequence", type="primary"):
                try:
                    engine.dispose()
                    with open(DB_FILE, "wb") as f:
                        f.write(uploaded_db.getbuffer())
                    st.success("Database re-initialized from backup stream safely. Please refresh the page parameters.")
                except Exception as e:
                    st.error(f"Database rewrite pipeline locked: {e}")
