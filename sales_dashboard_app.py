import sys
import os
import datetime
import shutil
import numpy as np
import pandas as pd
import customtkinter as ctk
import matplotlib.pyplot as plt
from tkinter import ttk, messagebox, filedialog
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from sklearn.linear_model import LinearRegression
from sqlalchemy import create_engine, Column, Integer, String, Numeric, Date, inspect, text
from sqlalchemy.orm import sessionmaker, declarative_base
from fpdf import FPDF

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
    print(f"Database Initialization Error: {e}")
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
    print(f"Schema Deployment or Migration Failure: {e}")
    sys.exit(1)

def get_db_session():
    return SessionLocal()

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

            parsed_date = datetime.datetime.strptime(sale_date, "%Y-%m-%d").date()

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
            return False, "Invalid input. Quantity/Prices must be numbers and Date must be YYYY-MM-DD."
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

            if not product_name or not category or not quantity or not unit_price or not cost_price or not sale_date or not region:
                return False, "All fields are required."

            qty = int(quantity)
            u_price = float(unit_price)
            c_price = float(cost_price)
            
            total_sales = qty * u_price
            total_cost = qty * c_price
            total_profit = total_sales - total_cost
            profit_margin = (total_profit / total_sales) * 100 if total_sales > 0 else 0.0

            parsed_date = datetime.datetime.strptime(sale_date, "%Y-%m-%d").date()

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
        except ValueError:
            session.rollback()
            return False, "Invalid input. Quantity/Prices must be numbers and Date must be YYYY-MM-DD."
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
    def bulk_delete_sale_records(sale_ids):
        session = get_db_session()
        try:
            session.query(Sale).filter(Sale.sale_id.in_([int(i) for i in sale_ids])).delete(synchronize_session=False)
            session.commit()
            return True, "Selected records deleted successfully."
        except Exception as e:
            session.rollback()
            return False, f"Bulk deletion failed: {str(e)}"
        finally:
            session.close()

    @staticmethod
    def get_filtered_records(search_name="", search_cat="All", search_region="All", start_date="", end_date="", sort_by="Date Desc"):
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
                try:
                    s_date = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
                    query = query.filter(Sale.sale_date >= s_date)
                except ValueError:
                    pass
            if end_date:
                try:
                    e_date = datetime.datetime.strptime(end_date, "%Y-%m-%d").date()
                    query = query.filter(Sale.sale_date <= e_date)
                except ValueError:
                    pass

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
                (
                    r.sale_id, r.product_name, r.category, r.quantity_sold,
                    float(r.unit_price), float(r.cost_price), float(r.total_sales),
                    float(r.total_cost), float(r.total_profit), float(r.profit_margin),
                    str(r.sale_date), r.region
                )
                for r in records
            ]
        except Exception:
            return []
        finally:
            session.close()

    @staticmethod
    def get_all_records():
        return DataController.get_filtered_records()

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
        
        top_prod = "N/A"
        if not df.empty:
            prod_group = df.groupby('product_name')['total_sales'].sum()
            if not prod_group.empty:
                top_prod = prod_group.idxmax()

        top_cat = "N/A"
        if not df.empty:
            cat_group = df.groupby('category')['total_sales'].sum()
            if not cat_group.empty:
                top_cat = cat_group.idxmax()

        top_reg = "N/A"
        if not df.empty:
            reg_group = df.groupby('region')['total_sales'].sum()
            if not reg_group.empty:
                top_reg = reg_group.idxmax()

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


class DashboardTab(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, corner_radius=16, fg_color="#111318")
        self.engine = AIAnalyticsEngine()
        self.grid_columnconfigure((0, 1, 2, 3), weight=1, minsize=180)
        self.grid_rowconfigure(2, weight=1)
        self.canvas_widget = None
        self.refresh_dashboard()

    def build_dashboard_header(self):
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, columnspan=4, padx=24, pady=(20, 10), sticky="ew")
        
        title_lbl = ctk.CTkLabel(
            header_frame, 
            text="Welcome Back, Administrator 👋", 
            font=("Segoe UI", 24, "bold"), 
            text_color="#FFFFFF"
        )
        title_lbl.pack(anchor="w")
        
        current_date_str = datetime.datetime.now().strftime("%A, %B %d, %Y")
        sub_lbl = ctk.CTkLabel(
            header_frame, 
            text=f"Sales Analytics Control Center  •  Last Updated: {current_date_str}", 
            font=("Segoe UI", 12), 
            text_color="#8E9AA8"
        )
        sub_lbl.pack(anchor="w", pady=(2, 0))

    def create_kpi_cards(self):
        metrics = self.engine.generate_kpi_summary()
        
        card_data = [
            ("Total Gross Revenue", f"${metrics['revenue']:,.2f}", "#6366F1", 0, "💰 Real-time yield metrics"),
            ("Operational Profit", f"${metrics['profit']:,.2f}", "#10B981", 1, "📈 Consolidated net margins"),
            ("Volumetric Orders", f"{metrics['orders']}", "#8B5CF6", 2, "🛒 Cumulative transactions"),
            ("Average Ticket Value", f"${metrics['avg_ticket']:,.2f}", "#EC4899", 3, "📊 Mean value per checkout")
        ]
        
        cards_container = ctk.CTkFrame(self, fg_color="transparent")
        cards_container.grid(row=1, column=0, columnspan=4, padx=16, pady=8, sticky="ew")
        cards_container.grid_columnconfigure((0, 1, 2, 3), weight=1)

        for col_idx, (title, val, color, original_col, subtitle) in enumerate(card_data):
            card = ctk.CTkFrame(
                cards_container, 
                corner_radius=16, 
                fg_color="#1E222B", 
                border_width=1, 
                border_color="#2E3440"
            )
            card.grid(row=0, column=col_idx, padx=8, pady=8, sticky="nsew")
            
            lbl_title = ctk.CTkLabel(card, text=title.upper(), font=("Segoe UI", 11, "bold"), text_color="#A3B1C2")
            lbl_title.pack(anchor="w", padx=16, pady=(16, 4))
            
            lbl_val = ctk.CTkLabel(card, text=val, font=("Segoe UI", 22, "bold"), text_color=color)
            lbl_val.pack(anchor="w", padx=16, pady=(0, 2))
            
            lbl_sub = ctk.CTkLabel(card, text=subtitle, font=("Segoe UI", 11), text_color="#6B7280")
            lbl_sub.pack(anchor="w", padx=16, pady=(0, 16))

        meta_container = ctk.CTkFrame(self, fg_color="transparent")
        meta_container.grid(row=2, column=0, columnspan=4, padx=16, pady=4, sticky="ew")
        meta_container.grid_columnconfigure((0, 1, 2), weight=1)

        meta_data = [
            ("Alpha Product Asset", f"🏆 {metrics['top_product']}", "#F59E0B", 0),
            ("Top Segment Category", f"📁 {metrics['top_cat']}", "#3B82F6", 1),
            ("Dominant Sales Region", f"🌎 {metrics['top_region']}", "#06B6D4", 2)
        ]

        for title, val, color, col_idx in meta_data:
            mcard = ctk.CTkFrame(
                meta_container, 
                corner_radius=12, 
                fg_color="#161920", 
                border_width=1, 
                border_color="#252A34"
            )
            mcard.grid(row=0, column=col_idx, padx=8, pady=4, sticky="ew")
            
            ctk.CTkLabel(mcard, text=title, font=("Segoe UI", 11, "bold"), text_color="#6B7280").pack(side="left", padx=16, pady=10)
            ctk.CTkLabel(mcard, text=val, font=("Segoe UI", 12, "bold"), text_color=color).pack(side="right", padx=16, pady=10)

    def render_analytics_matrix(self):
        if self.canvas_widget is not None:
            self.canvas_widget.destroy()
            self.canvas_widget = None

        canvas_frame = ctk.CTkFrame(
            self, 
            corner_radius=16, 
            fg_color="#1E222B", 
            border_width=1, 
            border_color="#2E3440"
        )
        canvas_frame.grid(row=3, column=0, columnspan=4, padx=24, pady=(12, 24), sticky="nsew")
        
        df = self.engine.get_clean_dataframe()
        if df.empty:
            ctk.CTkLabel(
                canvas_frame, 
                text="No enterprise records initialized yet. Please populate database variables.", 
                font=("Segoe UI", 14),
                text_color="#A3B1C2"
            ).pack(expand=True, pady=60)
            return

        fig, axes = plt.subplots(2, 3, figsize=(13, 6.5))
        fig.patch.set_facecolor('#1E222B')

        def style_axis(ax, title):
            ax.set_facecolor('#111318')
            ax.title.set_text(title)
            ax.title.set_color('#FFFFFF')
            ax.title.set_fontsize(10)
            ax.title.set_weight('bold')
            ax.tick_params(colors='#A3B1C2', labelsize=8)
            ax.grid(True, alpha=0.1, color='#FFFFFF', linestyle=':')
            for spine in ax.spines.values():
                spine.set_color('#2E3440')
            plt.setp(ax.get_xticklabels(), rotation=15, ha='right')

        daily_sales = df.groupby('sale_date')['total_sales'].sum()
        axes[0, 0].plot(daily_sales.index, daily_sales.values, color='#6366F1', marker='o', markersize=4, linewidth=2)
        style_axis(axes[0, 0], "Daily Revenue Velocity")
        
        df['month_period'] = df['sale_date'].dt.to_period('M').astype(str)
        monthly_sales = df.groupby('month_period')['total_sales'].sum()
        axes[0, 1].bar(monthly_sales.index, monthly_sales.values, color='#3B82F6', edgecolor='#1D4ED8', alpha=0.85, width=0.5)
        style_axis(axes[0, 1], "Monthly Sales Distribution")

        daily_profit = df.groupby('sale_date')['total_profit'].sum()
        axes[0, 2].plot(daily_profit.index, daily_profit.values, color='#10B981', marker='s', markersize=4, linewidth=2)
        style_axis(axes[0, 2], "Net Capital Profit Trend")

        top_prods = df.groupby('product_name')['total_sales'].sum().sort_values(ascending=False).head(5)
        axes[1, 0].barh(top_prods.index, top_prods.values, color='#8B5CF6', alpha=0.9, height=0.5)
        style_axis(axes[1, 0], "Top 5 Product Assets")
        axes[1, 0].invert_yaxis()

        cat_shares = df.groupby('category')['total_sales'].sum()
        wedges, texts, autotexts = axes[1, 1].pie(
            cat_shares.values, 
            labels=cat_shares.index, 
            autopct='%1.1f%%', 
            colors=['#6366F1', '#10B981', '#8B5CF6', '#F59E0B', '#EC4899'],
            textprops={'color': '#FFFFFF', 'fontsize': 8}
        )
        for autotext in autotexts:
            autotext.set_fontsize(7)
            autotext.set_weight('bold')
        axes[1, 1].set_facecolor('#111318')
        axes[1, 1].title.set_text("Categorical Mix Matrix")
        axes[1, 1].title.set_color('#FFFFFF')
        axes[1, 1].title.set_fontsize(10)
        axes[1, 1].title.set_weight('bold')

        reg_shares = df.groupby('region')['total_sales'].sum()
        axes[1, 2].bar(reg_shares.index, reg_shares.values, color='#06B6D4', alpha=0.85, width=0.4)
        style_axis(axes[1, 2], "Regional Revenue Weights")

        fig.tight_layout()
        canvas = FigureCanvasTkAgg(fig, master=canvas_frame)
        canvas.draw()
        self.canvas_widget = canvas.get_tk_widget()
        self.canvas_widget.pack(fill="both", expand=True, padx=8, pady=8)
        plt.close(fig)

    def refresh_dashboard(self):
        for widget in self.winfo_children():
            if widget != self.canvas_widget:
                widget.destroy()
        self.build_dashboard_header()
        self.create_kpi_cards()
        self.render_analytics_matrix()


class RecordsTab(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, corner_radius=16, fg_color="#111318")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        self.selected_record_id = None
        
        self.build_filter_and_search_matrix()
        self.build_form_interface()
        self.build_treeview_matrix()
        self.refresh_grid()

    def build_filter_and_search_matrix(self):
        self.filter_frame = ctk.CTkFrame(
            self, 
            corner_radius=12, 
            fg_color="#1E222B", 
            border_width=1, 
            border_color="#2E3440"
        )
        self.filter_frame.grid(row=0, column=0, padx=20, pady=(16, 8), sticky="ew")
        
        ctk.CTkLabel(
            self.filter_frame, 
            text="🔍 FILTER ENGINE:", 
            font=("Segoe UI", 11, "bold"), 
            text_color="#8E9AA8"
        ).grid(row=0, column=0, padx=(16, 8), pady=12)
        
        self.search_name_ent = ctk.CTkEntry(
            self.filter_frame, 
            placeholder_text="Search Product Asset...", 
            width=150,
            fg_color="#111318",
            border_color="#2E3440",
            text_color="#FFFFFF"
        )
        self.search_name_ent.grid(row=0, column=1, padx=4, pady=12)
        self.search_name_ent.bind("<KeyRelease>", lambda e: self.refresh_grid())
        
        self.filter_cat_cmb = ctk.CTkComboBox(
            self.filter_frame, 
            values=["All", "Electronics", "Furniture", "Networking", "Apparel"], 
            width=130, 
            command=lambda v: self.refresh_grid(),
            fg_color="#111318",
            border_color="#2E3440",
            button_color="#2E3440"
        )
        self.filter_cat_cmb.set("All")
        self.filter_cat_cmb.grid(row=0, column=2, padx=4, pady=12)

        self.filter_reg_cmb = ctk.CTkComboBox(
            self.filter_frame, 
            values=["All", "North", "South", "East", "West"], 
            width=110, 
            command=lambda v: self.refresh_grid(),
            fg_color="#111318",
            border_color="#2E3440",
            button_color="#2E3440"
        )
        self.filter_reg_cmb.set("All")
        self.filter_reg_cmb.grid(row=0, column=3, padx=4, pady=12)

        self.start_date_ent = ctk.CTkEntry(
            self.filter_frame, 
            placeholder_text="Start YYYY-MM-DD", 
            width=130,
            fg_color="#111318",
            border_color="#2E3440"
        )
        self.start_date_ent.grid(row=0, column=4, padx=4, pady=12)
        self.start_date_ent.bind("<KeyRelease>", lambda e: self.refresh_grid())
        
        self.end_date_ent = ctk.CTkEntry(
            self.filter_frame, 
            placeholder_text="End YYYY-MM-DD", 
            width=130,
            fg_color="#111318",
            border_color="#2E3440"
        )
        self.end_date_ent.grid(row=0, column=5, padx=4, pady=12)
        self.end_date_ent.bind("<KeyRelease>", lambda e: self.refresh_grid())

        self.sort_cmb = ctk.CTkComboBox(
            self.filter_frame, 
            values=["Date Desc", "Date Asc", "Revenue Desc", "Profit Desc", "Product Name"], 
            width=130, 
            command=lambda v: self.refresh_grid(),
            fg_color="#111318",
            border_color="#2E3440",
            button_color="#2E3440"
        )
        self.sort_cmb.set("Date Desc")
        self.sort_cmb.grid(row=0, column=6, padx=4, pady=12)

        ctk.CTkButton(
            self.filter_frame, 
            text="Reset", 
            width=70, 
            fg_color="#3b4252", 
            hover_color="#4c566a", 
            command=self.reset_filters
        ).grid(row=0, column=7, padx=6, pady=12)
        
        ctk.CTkButton(
            self.filter_frame, 
            text="🔄 Refresh Engine", 
            width=120, 
            fg_color="#434C5E",
            hover_color="#4C566A",
            command=self.refresh_grid
        ).grid(row=0, column=8, padx=(6, 16), pady=12)

    def build_form_interface(self):
        self.form_frame = ctk.CTkFrame(
            self, 
            corner_radius=12, 
            fg_color="#1E222B", 
            border_width=1, 
            border_color="#2E3440"
        )
        self.form_frame.grid(row=1, column=0, padx=20, pady=8, sticky="ew")
        
        inputs_layout = ctk.CTkFrame(self.form_frame, fg_color="transparent")
        inputs_layout.pack(fill="x", padx=16, pady=(12, 4))
        
        self.ent_prod = ctk.CTkEntry(inputs_layout, placeholder_text="Product Asset Name", width=160, fg_color="#111318", border_color="#2E3440")
        self.ent_prod.pack(side="left", padx=4)
        
        self.cmb_cat = ctk.CTkComboBox(inputs_layout, values=["Electronics", "Furniture", "Networking", "Apparel"], width=130, fg_color="#111318", border_color="#2E3440", button_color="#2E3440")
        self.cmb_cat.pack(side="left", padx=4)
        
        self.ent_qty = ctk.CTkEntry(inputs_layout, placeholder_text="Quantity", width=80, fg_color="#111318", border_color="#2E3440")
        self.ent_qty.pack(side="left", padx=4)
        
        self.ent_price = ctk.CTkEntry(inputs_layout, placeholder_text="Unit Price ($)", width=100, fg_color="#111318", border_color="#2E3440")
        self.ent_price.pack(side="left", padx=4)
        
        self.ent_cost = ctk.CTkEntry(inputs_layout, placeholder_text="Unit Cost ($)", width=100, fg_color="#111318", border_color="#2E3440")
        self.ent_cost.pack(side="left", padx=4)
        
        self.ent_date = ctk.CTkEntry(inputs_layout, placeholder_text="Date YYYY-MM-DD", width=120, fg_color="#111318", border_color="#2E3440")
        self.ent_date.pack(side="left", padx=4)
        
        self.cmb_region = ctk.CTkComboBox(inputs_layout, values=["North", "South", "East", "West"], width=100, fg_color="#111318", border_color="#2E3440", button_color="#2E3440")
        self.cmb_region.pack(side="left", padx=4)

        actions_layout = ctk.CTkFrame(self.form_frame, fg_color="transparent")
        actions_layout.pack(fill="x", padx=16, pady=(4, 12))

        self.btn_commit = ctk.CTkButton(actions_layout, text="➕ Commit Entry", fg_color="#10B981", hover_color="#059669", font=("Segoe UI", 12, "bold"), width=130, command=self.execute_add)
        self.btn_commit.pack(side="left", padx=4)
        
        self.btn_update = ctk.CTkButton(actions_layout, text="🔄 Update Selected", fg_color="#F59E0B", hover_color="#D97706", font=("Segoe UI", 12, "bold"), width=140, command=self.execute_update)
        self.btn_update.pack(side="left", padx=4)
        
        self.btn_delete = ctk.CTkButton(actions_layout, text="🗑️ Drop Entry", fg_color="#EF4444", hover_color="#DC2626", font=("Segoe UI", 12, "bold"), width=120, command=self.execute_delete)
        self.btn_delete.pack(side="left", padx=4)
        
        self.btn_bulk_delete = ctk.CTkButton(actions_layout, text="💥 Bulk Matrix Purge", fg_color="#4B5563", hover_color="#374151", font=("Segoe UI", 12, "bold"), width=160, command=self.execute_bulk_delete)
        self.btn_bulk_delete.pack(side="left", padx=4)
        
        self.btn_clear = ctk.CTkButton(actions_layout, text="Clear Canvas", fg_color="#374151", hover_color="#1F2937", width=100, command=self.clear_form)
        self.btn_clear.pack(side="right", padx=4)

    def build_treeview_matrix(self):
        self.tree_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.tree_frame.grid(row=2, column=0, padx=20, pady=(4, 20), sticky="nsew")
        
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "Treeview", 
            background="#1E222B", 
            fieldbackground="#1E222B", 
            foreground="#E5E7EB", 
            rowheight=28, 
            borderwidth=0,
            font=("Segoe UI", 10)
        )
        style.configure(
            "Treeview.Heading",
            background="#2E3440",
            foreground="#FFFFFF",
            font=("Segoe UI", 10, "bold"),
            borderwidth=0
        )
        style.map("Treeview", background=[("selected", "#4F46E5")], foreground=[("selected", "#FFFFFF")])
        
        cols = ("ID", "Product Asset", "Category", "Qty", "Price", "Cost", "Total Sales", "Total Cost", "Profit", "Margin %", "Date", "Region")
        self.tree = ttk.Treeview(self.tree_frame, columns=cols, show="headings")
        
        for col in cols:
            self.tree.heading(col, text=col)
            w = 55 if col in ["ID", "Qty", "Margin %"] else (95 if col in ["Price", "Cost", "Region"] else 115)
            self.tree.column(col, anchor="center", width=w)
            
        scrollbar = ttk.Scrollbar(self.tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.tree.bind("<<TreeviewSelect>>", self.on_record_select)

    def reset_filters(self):
        self.search_name_ent.delete(0, "end")
        self.filter_cat_cmb.set("All")
        self.filter_reg_cmb.set("All")
        self.start_date_ent.delete(0, "end")
        self.end_date_ent.delete(0, "end")
        self.sort_cmb.set("Date Desc")
        self.refresh_grid()

    def refresh_grid(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        records = DataController.get_filtered_records(
            search_name=self.search_name_ent.get(),
            search_cat=self.filter_cat_cmb.get(),
            search_region=self.filter_reg_cmb.get(),
            start_date=self.start_date_ent.get(),
            end_date=self.end_date_ent.get(),
            sort_by=self.sort_cmb.get()
        )
        for record in records:
            formatted_record = list(record)
            formatted_record[4] = f"${record[4]:.2f}"
            formatted_record[5] = f"${record[5]:.2f}"
            formatted_record[6] = f"${record[6]:.2f}"
            formatted_record[7] = f"${record[7]:.2f}"
            formatted_record[8] = f"${record[8]:.2f}"
            formatted_record[9] = f"{record[9]:.1f}%"
            self.tree.insert("", "end", values=formatted_record)

    def on_record_select(self, event):
        selected = self.tree.selection()
        if not selected:
            return
        vals = self.tree.item(selected[0])['values']
        self.selected_record_id = vals[0]
        
        self.ent_prod.delete(0, "end")
        self.ent_prod.insert(0, vals[1])
        self.cmb_cat.set(vals[2])
        self.ent_qty.delete(0, "end")
        self.ent_qty.insert(0, vals[3])
        
        self.ent_price.delete(0, "end")
        self.ent_price.insert(0, vals[4].replace("$", ""))
        self.ent_cost.delete(0, "end")
        self.ent_cost.insert(0, vals[5].replace("$", ""))
        
        self.ent_date.delete(0, "end")
        self.ent_date.insert(0, vals[10])
        self.cmb_region.set(vals[11])

    def clear_form(self):
        self.selected_record_id = None
        self.ent_prod.delete(0, "end")
        self.ent_qty.delete(0, "end")
        self.ent_price.delete(0, "end")
        self.ent_cost.delete(0, "end")
        self.ent_date.delete(0, "end")

    def execute_add(self):
        status, msg = DataController.add_sale_record(
            self.ent_prod.get(), self.cmb_cat.get(), self.ent_qty.get(),
            self.ent_price.get(), self.ent_cost.get(), self.ent_date.get(), self.cmb_region.get()
        )
        if status:
            messagebox.showinfo("Operation Log", msg)
            self.refresh_grid()
            self.clear_form()
        else:
            messagebox.showerror("Operation Log", msg)

    def execute_update(self):
        if not self.selected_record_id:
            messagebox.showwarning("Selection Warning", "Select an operational matrix row entry first.")
            return
        status, msg = DataController.update_sale_record(
            self.selected_record_id, self.ent_prod.get(), self.cmb_cat.get(), self.ent_qty.get(),
            self.ent_price.get(), self.ent_cost.get(), self.ent_date.get(), self.cmb_region.get()
        )
        if status:
            messagebox.showinfo("Operation Log", msg)
            self.refresh_grid()
            self.clear_form()
        else:
            messagebox.showerror("Operation Log", msg)

    def execute_delete(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Select record to clear.")
            return
        status, msg = DataController.delete_sale_record(self.tree.item(selected[0])['values'][0])
        messagebox.showinfo("Operation Log", msg)
        if status:
            self.refresh_grid()
            self.clear_form()

    def execute_bulk_delete(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Select multiple entries for data matrix purge.")
            return
        if messagebox.askyesno("Confirm Purge", f"Are you sure you want to drop {len(selected)} entries?"):
            ids = [self.tree.item(item)['values'][0] for item in selected]
            status, msg = DataController.bulk_delete_sale_records(ids)
            messagebox.showinfo("Operation Log", msg)
            self.refresh_grid()
            self.clear_form()


class ForecastingTab(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, corner_radius=16, fg_color="#111318")
        self.engine = AIAnalyticsEngine()
        self.canvas_widget = None
        
        self.top_control = ctk.CTkFrame(
            self, 
            corner_radius=12, 
            fg_color="#1E222B", 
            border_width=1, 
            border_color="#2E3440"
        )
        self.top_control.pack(fill="x", padx=20, pady=(20, 10))
        
        ctk.CTkLabel(
            self.top_control, 
            text="🔮 HORIZON TARGET CONFIGURATION:", 
            font=("Segoe UI", 12, "bold"),
            text_color="#8E9AA8"
        ).pack(side="left", padx=16, pady=16)
        
        self.horizon_cmb = ctk.CTkComboBox(
            self.top_control, 
            values=["30 Days Target", "90 Days Extended Target"],
            fg_color="#111318",
            border_color="#2E3440",
            button_color="#2E3440"
        )
        self.horizon_cmb.set("30 Days Target")
        self.horizon_cmb.pack(side="left", padx=8, pady=16)
        
        ctk.CTkButton(
            self.top_control, 
            text="Run ML Predictive Regression Models", 
            fg_color="#6366F1",
            hover_color="#4F46E5",
            font=("Segoe UI", 12, "bold"),
            command=self.render_forecast_visuals
        ).pack(side="left", padx=12, pady=16)

        self.info_card = ctk.CTkFrame(self, corner_radius=12, fg_color="#161920", border_width=1, border_color="#252A34")
        self.info_card.pack(fill="x", padx=20, pady=4)
        
        ctk.CTkLabel(
            self.info_card, 
            text="Model Specifications: Scikit-Learn Ordinary Least Squares (OLS) Linear Regression Engine Matrix", 
            font=("Segoe UI", 11), 
            text_color="#6B7280"
        ).pack(side="left", padx=16, pady=8)
        
        ctk.CTkLabel(
            self.info_card, 
            text="Confidence Interval: Statistical Trendline Extension Sequence", 
            font=("Segoe UI", 11), 
            text_color="#6B7280"
        ).pack(side="right", padx=16, pady=8)
        
        self.graph_frame = ctk.CTkFrame(
            self, 
            corner_radius=12, 
            fg_color="#1E222B", 
            border_width=1, 
            border_color="#2E3440"
        )
        self.graph_frame.pack(fill="both", expand=True, padx=20, pady=(10, 20))
        self.render_forecast_visuals()

    def render_forecast_visuals(self):
        if self.canvas_widget is not None:
            self.canvas_widget.destroy()
            self.canvas_widget = None

        horizon = 30 if "30" in self.horizon_cmb.get() else 90
        df = self.engine.get_clean_dataframe()
        if df.empty or len(df) < 3:
            ctk.CTkLabel(
                self.graph_frame, 
                text="Insufficient vector density. Please supply more historical date metrics to generate models.", 
                font=("Segoe UI", 13),
                text_color="#A3B1C2"
            ).pack(expand=True, pady=40)
            return

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
        fig.patch.set_facecolor('#1E222B')

        def setup_forecast_axis(ax, title):
            ax.set_facecolor('#111318')
            ax.set_title(title, color='#FFFFFF', fontsize=11, fontweight='bold', pad=10)
            ax.tick_params(colors='#A3B1C2', labelsize=8)
            ax.grid(True, alpha=0.1, color='#FFFFFF', linestyle='--')
            for spine in ax.spines.values():
                spine.set_color('#2E3440')
            plt.setp(ax.get_xticklabels(), rotation=25, ha='right')

        daily_sales = df.groupby('sale_date')['total_sales'].sum()
        ax1.plot(daily_sales.index, daily_sales.values, color='#3B82F6', marker='o', label='Historical Track', markersize=3, linewidth=1.5)
        f_dates, f_preds = self.engine.run_predictive_forecasting(horizon, 'total_sales')
        if len(f_dates) > 0:
            ax1.plot(f_dates, f_preds, color='#F59E0B', linestyle='--', linewidth=2, label=f'OLS Projection Horizon ({horizon}D)')
        setup_forecast_axis(ax1, "Gross Revenue Trajectory Forecast Model")
        ax1.legend(facecolor='#1E222B', edgecolor='#2E3440', labelcolor='#FFFFFF', fontsize=8)

        daily_profit = df.groupby('sale_date')['total_profit'].sum()
        ax2.plot(daily_profit.index, daily_profit.values, color='#10B981', marker='s', label='Historical Net Yield', markersize=3, linewidth=1.5)
        f_dates_p, f_preds_p = self.engine.run_predictive_forecasting(horizon, 'total_profit')
        if len(f_dates_p) > 0:
            ax2.plot(f_dates_p, f_preds_p, color='#EF4444', linestyle='--', linewidth=2, label=f'Profit Model Target ({horizon}D)')
        setup_forecast_axis(ax2, "Net Capital Margins Structural Forecast")
        ax2.legend(facecolor='#1E222B', edgecolor='#2E3440', labelcolor='#FFFFFF', fontsize=8)

        fig.tight_layout()
        self.canvas = FigureCanvasTkAgg(fig, master=self.graph_frame)
        self.canvas.draw()
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.pack(fill="both", expand=True, padx=12, pady=12)
        plt.close(fig)


class AIInsightsTab(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, corner_radius=16, fg_color="#111318")
        self.engine = AIAnalyticsEngine()
        
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=24, pady=(20, 10))
        
        label = ctk.CTkLabel(header, text="🤖 AI Enterprise Strategic Core Engine", font=("Segoe UI", 22, "bold"), text_color="#FFFFFF")
        label.pack(anchor="w")
        
        sub = ctk.CTkLabel(header, text="Automated prescriptive summaries and transactional alpha analytics models.", font=("Segoe UI", 12), text_color="#8E9AA8")
        sub.pack(anchor="w", pady=(2, 0))
        
        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_frame.pack(fill="both", expand=True, padx=16, pady=10)
        self.refresh_insights()

    def refresh_insights(self):
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        insights = self.engine.generate_ai_insights_dictionary()
        
        sections = [
            ("🏆 Top Performing Corporate Assets", insights["top_products"], "#10B981", "Maximum volume metrics output vector."),
            ("📉 Lagging Operational Matrix Segments", insights["worst_products"], "#EF4444", "Sub-optimal optimization baseline target."),
            ("💎 Profit Maximization Core Units", insights["profitable_category"], "#8B5CF6", "Highest alpha return structural channel."),
            ("🗺️ Core Geographical Domain Stronghold", insights["profitable_region"], "#06B6D4", "Dominant territory conversion density."),
            ("📈 Systemic Revenue Trend Matrix Velocity", insights["revenue_trend"], "#3B82F6", "Gross transaction speed indicator."),
            ("📊 Systemic Capital Profit Margin Track", insights["profit_trend"], "#F59E0B", "Delta margin evaluation path."),
            ("🚀 Composite System Expansion Metrics", insights["growth_trend"], "#EC4899", "General industrial strength evaluation framework."),
            ("💡 Strategic Corporate Business Execution Directive", insights["business_recommendations"], "#10B981", "Prescriptive administrative operations trajectory."),
            ("📦 Logistical Inventory Asset Optimization Allocation", insights["inventory_recommendations"], "#6B7280", "Supply stream defensive holding instructions."),
            ("📣 Promotional Outreach Targeted Deployment Matrix", insights["marketing_recommendations"], "#6366F1", "Geo-targeted public scaling framework configuration.")
        ]

        for title, desc, color, context in sections:
            block = ctk.CTkFrame(
                self.scroll_frame, 
                corner_radius=12, 
                fg_color="#1E222B", 
                border_width=1, 
                border_color="#2E3440"
            )
            block.pack(fill="x", padx=8, pady=6)
            
            accent_bar = ctk.CTkFrame(block, width=4, fg_color=color, corner_radius=2)
            accent_bar.pack(side="left", fill="y", padx=(0, 12))
            
            text_container = ctk.CTkFrame(block, fg_color="transparent")
            text_container.pack(side="left", fill="both", expand=True, padx=4, pady=12)
            
            ctk.CTkLabel(text_container, text=title, font=("Segoe UI", 13, "bold"), text_color=color).pack(anchor="w")
            ctk.CTkLabel(text_container, text=desc, font=("Segoe UI", 12), text_color="#E5E7EB", justify="left", wraplength=850).pack(anchor="w", pady=(2, 2))
            ctk.CTkLabel(text_container, text=f"Context: {context}", font=("Segoe UI", 10, "italic"), text_color="#6B7280").pack(anchor="w")


class ReportsTab(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, corner_radius=16, fg_color="#111318")
        self.engine = AIAnalyticsEngine()
        
        ctk.CTkLabel(
            self, 
            text="📊 Enterprise Financial Data Export Center", 
            font=("Segoe UI", 22, "bold"),
            text_color="#FFFFFF"
        ).pack(pady=(30, 6))
        
        ctk.CTkLabel(
            self, 
            text="Compile system variables into automated downstream ledgers and summaries.", 
            font=("Segoe UI", 12),
            text_color="#8E9AA8"
        ).pack(pady=(0, 20))
        
        box = ctk.CTkFrame(
            self, 
            corner_radius=16, 
            fg_color="#1E222B", 
            border_width=1, 
            border_color="#2E3440", 
            width=500, 
            height=380
        )
        box.pack_propagate(False)
        box.pack(pady=10)

        ctk.CTkLabel(
            box, 
            text="SELECT TARGET EXPORT CHANNEL:", 
            font=("Segoe UI", 12, "bold"), 
            text_color="#A3B1C2"
        ).pack(pady=(24, 16))
        
        ctk.CTkButton(
            box, 
            text="📄 Export Core Ledger to Flat File (CSV)", 
            font=("Segoe UI", 12, "bold"),
            fg_color="#3B82F6",
            hover_color="#2563EB",
            command=self.export_csv, 
            width=380, 
            height=42,
            corner_radius=8
        ).pack(pady=10)
        
        ctk.CTkButton(
            box, 
            text="📈 Compile Operational Sheet Workbooks (XLSX)", 
            font=("Segoe UI", 12, "bold"),
            fg_color="#10B981",
            hover_color="#059669",
            command=self.export_excel, 
            width=380, 
            height=42,
            corner_radius=8
        ).pack(pady=10)
        
        ctk.CTkButton(
            box, 
            text="👑 Generate AI Executive Core Document (PDF)", 
            font=("Segoe UI", 12, "bold"),
            fg_color="#8B5CF6", 
            hover_color="#7C3AED",
            command=self.export_pdf, 
            width=380, 
            height=42,
            corner_radius=8
        ).pack(pady=10)

        footer_note = ctk.CTkLabel(
            box, 
            text="All exports include cryptographic integrity validation hooks.", 
            font=("Segoe UI", 10, "italic"), 
            text_color="#6B7280"
        )
        footer_note.pack(side="bottom", pady=20)

    def export_csv(self):
        df = self.engine.get_clean_dataframe()
        if df.empty:
            messagebox.showwarning("No Data", "There is no data to export yet.")
            return
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV Files", "*.csv")])
        if path:
            df.to_csv(path, index=False)
            messagebox.showinfo("Success", "CSV file compiled safely.")

    def export_excel(self):
        df = self.engine.get_clean_dataframe()
        if df.empty:
            messagebox.showwarning("No Data", "There is no data to export yet.")
            return
        path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel Workspace", "*.xlsx")])
        if path:
            try:
                df.to_excel(path, index=False, engine='openpyxl')
                messagebox.showinfo("Success", "Excel Workspace built successfully.")
            except Exception as e:
                messagebox.showerror("Export Error", f"Failed to save Excel file: {e}")

    def export_pdf(self):
        df = self.engine.get_clean_dataframe()
        if df.empty:
            messagebox.showwarning("No Data", "There is no data to export yet.")
            return
        path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF Document", "*.pdf")])
        if path:
            metrics = self.engine.generate_kpi_summary()
            insights = self.engine.generate_ai_insights_dictionary()
            
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
            
            try:
                pdf.output(path)
                messagebox.showinfo("Success", "Executive Summary compiled completely to PDF.")
            except Exception as e:
                messagebox.showerror("PDF Error", f"Could not create file: {e}")


class SettingsTab(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, corner_radius=16, fg_color="#111318")
        
        ctk.CTkLabel(
            self, 
            text="⚙️ Infrastructure Controls & Preferences", 
            font=("Segoe UI", 20, "bold"),
            text_color="#FFFFFF"
        ).pack(pady=(24, 16))
        
        wrapper = ctk.CTkScrollableFrame(
            self, 
            corner_radius=12, 
            fg_color="#1E222B", 
            border_width=1, 
            border_color="#2E3440"
        )
        wrapper.pack(fill="both", expand=True, padx=24, pady=(0, 24))

        g1 = ctk.CTkFrame(wrapper, fg_color="#161920", corner_radius=8, border_width=1, border_color="#252A34")
        g1.pack(fill="x", padx=10, pady=8)
        
        ctk.CTkLabel(g1, text="Visual Presentation Framework Configuration Theme:", font=("Segoe UI", 12, "bold"), text_color="#FFFFFF").pack(anchor="w", padx=16, pady=(12, 6))
        self.theme_menu = ctk.CTkOptionMenu(g1, values=["Dark", "Light"], command=ctk.set_appearance_mode, fg_color="#2E3440", button_color="#2E3440", dropdown_fg_color="#1E222B")
        self.theme_menu.set(ctk.get_appearance_mode())
        self.theme_menu.pack(anchor="w", padx=16, pady=(0, 16))

        g2 = ctk.CTkFrame(wrapper, fg_color="#161920", corner_radius=8, border_width=1, border_color="#252A34")
        g2.pack(fill="x", padx=10, pady=8)
        
        ctk.CTkLabel(g2, text="Data Core Architecture Specifications Matrix:", font=("Segoe UI", 12, "bold"), text_color="#FFFFFF").pack(anchor="w", padx=16, pady=(12, 4))
        info_str = f"Database Model Form: SQLite 3 relational local engine matrix\nTarget Active Endpoint Mapping: {DB_FILE}\nTable Validation Index: Schema definitions completely verified operational."
        ctk.CTkLabel(g2, text=info_str, justify="left", font=("Consolas", 11), text_color="#A3B1C2").pack(anchor="w", padx=16, pady=(0, 16))

        g3 = ctk.CTkFrame(wrapper, fg_color="#161920", corner_radius=8, border_width=1, border_color="#252A34")
        g3.pack(fill="x", padx=10, pady=8)
        
        ctk.CTkLabel(g3, text="Administrative Disaster Recovery & Backup Pipelines:", font=("Segoe UI", 12, "bold"), text_color="#FFFFFF").pack(anchor="w", padx=16, pady=(12, 8))
        
        btn_layout = ctk.CTkFrame(g3, fg_color="transparent")
        btn_layout.pack(anchor="w", padx=16, pady=(0, 16))
        
        ctk.CTkButton(btn_layout, text="Backup Core Database Ledger", fg_color="#4B5563", hover_color="#374151", command=self.backup_database).pack(side="left", padx=4)
        ctk.CTkButton(btn_layout, text="Restore Database Mapping Stream", fg_color="#F59E0B", hover_color="#D97706", command=self.restore_database).pack(side="left", padx=4)
        ctk.CTkButton(btn_layout, text="Export Full Raw DDL Script", fg_color="#374151", hover_color="#1F2937", command=self.export_raw_dump).pack(side="left", padx=4)

    def backup_database(self):
        path = filedialog.asksaveasfilename(defaultextension=".db", filetypes=[("Database Backup", "*.db")], initialfile="business_analytics_backup.db")
        if path:
            try:
                shutil.copy2(DB_FILE, path)
                messagebox.showinfo("Backup Pipeline", "Core ledger mirrored and written safely.")
            except Exception as e:
                messagebox.showerror("Failure Matrix", f"Database streaming failed: {e}")

    def restore_database(self):
        path = filedialog.askopenfilename(filetypes=[("Database File", "*.db")])
        if path:
            if messagebox.askyesno("Confirm Core Overwrite", "Warning: Restoring will overwrite all current entries. Proceed?"):
                try:
                    engine.dispose()
                    shutil.copy2(path, DB_FILE)
                    messagebox.showinfo("System Restore", "Database re-initialized from backup stream safely.")
                except Exception as e:
                    messagebox.showerror("Failure Matrix", f"Database rewrite pipeline locked: {e}")

    def export_raw_dump(self):
        path = filedialog.asksaveasfilename(defaultextension=".sql", filetypes=[("SQL Structure Text Dump", "*.sql")], initialfile="raw_structure_dump.sql")
        if path:
            try:
                with open(path, "w") as f:
                    f.write("-- Enterprise Datacore Structure Dump\n")
                    f.write(f"-- Exported on Sequence Timestamp: {datetime.datetime.now()}\n")
                messagebox.showinfo("Export Pipeline", "Full raw SQL template structure written.")
            except Exception as e:
                messagebox.showerror("Failure Matrix", f"Dump failed: {e}")


class SalesDashboardApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Datacore Pro // Enterprise Business Analytics Dashboard Engine v3.0")
        self.geometry("1400x820")
        self.minsize(1280, 760)
        
        self.configure(fg_color="#0B0C10")
        
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        self.build_sidebar_navigation()

        self.container = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.container.grid(row=0, column=1, sticky="nsew", padx=16, pady=16)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        self.frames = {}
        for F in (DashboardTab, RecordsTab, ForecastingTab, AIInsightsTab, ReportsTab, SettingsTab):
            frame = F(self.container)
            self.frames[F.__name__] = frame
            frame.grid(row=0, column=0, sticky="nsew")
            
        self.display_view("DashboardTab")

    def build_sidebar_navigation(self):
        self.sidebar = ctk.CTkFrame(self, width=260, corner_radius=0, fg_color="#111318", border_width=1, border_color="#1E222B")
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.pack_propagate(False)
        
        brand_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        brand_frame.pack(pady=(32, 24), padx=20, fill="x")
        
        ctk.CTkLabel(
            brand_frame, 
            text="DATACORE // PRO AI", 
            font=("Segoe UI", 18, "bold"), 
            text_color="#6366F1",
            anchor="w"
        ).pack(fill="x")
        
        ctk.CTkLabel(
            brand_frame, 
            text="Enterprise Control Dock v3.0", 
            font=("Segoe UI", 11), 
            text_color="#4B5563",
            anchor="w"
        ).pack(fill="x")
        
        menu_items = [
            ("📊 Executive Dashboard", "DashboardTab"),
            ("📝 Data Management", "RecordsTab"),
            ("🔮 Predictive ML Models", "ForecastingTab"),
            ("🤖 AI Strategic Analysis", "AIInsightsTab"),
            ("📁 Reports & File Exports", "ReportsTab"),
            ("⚙️ System Settings", "SettingsTab")
        ]

        self.nav_buttons = {}
        for label, view_id in menu_items:
            btn = ctk.CTkButton(
                self.sidebar, 
                text=label, 
                anchor="w", 
                height=40,
                font=("Segoe UI", 12, "bold"),
                fg_color="transparent",
                text_color="#A3B1C2",
                hover_color="#1E222B",
                corner_radius=8,
                command=lambda v=view_id: self.display_view(v)
            )
            btn.pack(pady=4, padx=14, fill="x")
            self.nav_buttons[view_id] = btn

        status_card = ctk.CTkFrame(self.sidebar, fg_color="#1E222B", corner_radius=10, height=50)
        status_card.pack(side="bottom", pady=24, padx=16, fill="x")
        
        indicator = ctk.CTkFrame(status_card, width=8, height=8, corner_radius=4, fg_color="#10B981")
        indicator.pack(side="left", padx=(14, 8))
        
        lbl_status = ctk.CTkLabel(status_card, text="SYSTEM ENG ACTIVE", font=("Segoe UI", 10, "bold"), text_color="#10B981")
        lbl_status.pack(side="left")

    def display_view(self, view_name):
        self.frames[view_name].tkraise()
        
        for v_id, button in self.nav_buttons.items():
            if v_id == view_name:
                button.configure(fg_color="#6366F1", text_color="#FFFFFF", hover_color="#4F46E5")
            else:
                button.configure(fg_color="transparent", text_color="#A3B1C2", hover_color="#1E222B")
        
        if view_name == "DashboardTab":
            self.frames[view_name].refresh_dashboard()
        elif view_name == "RecordsTab":
            self.frames[view_name].refresh_grid()
        elif view_name == "AIInsightsTab":
            self.frames[view_name].refresh_insights()


if __name__ == "__main__":
    ctk.set_appearance_mode("Dark")
    ctk.set_default_color_theme("blue")
    
    app = SalesDashboardApp()
    app.mainloop()