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

# ═══════════════════════════════════════════════════════════════════════════════
# 🎨 ELITE CSS ANIMATIONS & GLASSMORPHISM STYLING
# ═══════════════════════════════════════════════════════════════════════════════

ELITE_CSS_ANIMATIONS = """
<style>
    * {
        margin: 0;
        padding: 0;
        box-sizing: border-box;
    }

    /* ✨ ANIMATED LIQUID GRADIENT BACKGROUND */
    @keyframes liquidGradient {
        0% { background: linear-gradient(135deg, #0F172A 0%, #1E293B 25%, #0F172A 50%, #1E293B 100%); }
        25% { background: linear-gradient(135deg, #1E293B 0%, #0F172A 25%, #1E293B 50%, #0F172A 100%); }
        50% { background: linear-gradient(135deg, #0F172A 0%, #1E293B 25%, #0F172A 50%, #1E293B 100%); }
        75% { background: linear-gradient(135deg, #1E293B 0%, #0F172A 25%, #1E293B 50%, #0F172A 100%); }
        100% { background: linear-gradient(135deg, #0F172A 0%, #1E293B 25%, #0F172A 50%, #1E293B 100%); }
    }

    /* 🌊 SMOOTH FADE-IN ENTRANCE */
    @keyframes fadeInUp {
        0% {
            opacity: 0;
            transform: translateY(20px);
        }
        100% {
            opacity: 1;
            transform: translateY(0);
        }
    }

    /* 🎯 FADE-IN DOWN */
    @keyframes fadeInDown {
        0% {
            opacity: 0;
            transform: translateY(-20px);
        }
        100% {
            opacity: 1;
            transform: translateY(0);
        }
    }

    /* 💫 SUBTLE PULSING GLOW */
    @keyframes pulseGlow {
        0%, 100% {
            box-shadow: 0 0 20px rgba(99, 102, 241, 0.3), 
                        0 10px 30px rgba(0, 0, 0, 0.2);
        }
        50% {
            box-shadow: 0 0 40px rgba(99, 102, 241, 0.5), 
                        0 10px 30px rgba(0, 0, 0, 0.3);
        }
    }

    /* 🌟 NEON GLOW EFFECT */
    @keyframes neonGlow {
        0%, 100% {
            text-shadow: 0 0 10px rgba(99, 102, 241, 0.5);
            box-shadow: 0 0 15px rgba(99, 102, 241, 0.3);
        }
        50% {
            text-shadow: 0 0 20px rgba(99, 102, 241, 0.8);
            box-shadow: 0 0 25px rgba(99, 102, 241, 0.5);
        }
    }

    /* 🔮 FLOATING ANIMATION */
    @keyframes float {
        0%, 100% { transform: translateY(0px); }
        50% { transform: translateY(-10px); }
    }

    /* 🌈 GRADIENT BORDER ANIMATION */
    @keyframes gradientBorder {
        0% { border-color: rgba(99, 102, 241, 0.2); }
        50% { border-color: rgba(99, 102, 241, 0.6); }
        100% { border-color: rgba(99, 102, 241, 0.2); }
    }

    /* ═══════════════════════════════════════════════════════════════════════════ */
    /* MAIN PAGE BACKGROUND */
    /* ═══════════════════════════════════════════════════════════════════════════ */
    [data-testid="stAppViewContainer"] {
        background: linear-gradient(135deg, #0F172A 0%, #1E293B 50%, #0F172A 100%);
        animation: liquidGradient 15s ease-in-out infinite;
        background-size: 200% 200%;
    }

    /* ═══════════════════════════════════════════════════════════════════════════ */
    /* STREAMLIT HEADER & TITLE STYLING */
    /* ═══════════════════════════════════════════════════════════════════════════ */
    h1 {
        color: #F8FAFC !important;
        font-family: 'Segoe UI', Roboto, 'Helvetica Neue', sans-serif !important;
        font-weight: 700 !important;
        letter-spacing: 0.5px !important;
        animation: fadeInDown 0.8s ease-out !important;
        text-shadow: 0 4px 12px rgba(0, 0, 0, 0.3) !important;
    }

    h2 {
        color: #E2E8F0 !important;
        font-family: 'Segoe UI', Roboto, 'Helvetica Neue', sans-serif !important;
        animation: fadeInUp 0.8s ease-out !important;
    }

    h3 {
        color: #CBD5E1 !important;
        animation: fadeInUp 0.8s ease-out 0.1s backwards !important;
    }

    h4 {
        color: #818CF8 !important;
        animation: fadeInUp 0.8s ease-out 0.15s backwards !important;
    }

    /* ═══════════════════════════════════════════════════════════════════════════ */
    /* GLASSMORPHISM CARDS & CONTAINERS */
    /* ═══════════════════════════════════════════════════════════════════════════ */
    [data-testid="stMetricValue"] {
        font-size: 32px !important;
        color: #F8FAFC !important;
        animation: fadeInUp 0.8s ease-out backwards !important;
    }

    [data-testid="stMetricLabel"] {
        color: #94A3B8 !important;
        font-size: 14px !important;
        letter-spacing: 0.3px !important;
    }

    /* Metric Card Container */
    [data-testid="stMetric"] {
        background: rgba(15, 23, 42, 0.5) !important;
        border: 1px solid rgba(99, 102, 241, 0.15) !important;
        border-radius: 16px !important;
        padding: 24px !important;
        backdrop-filter: blur(10px) !important;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2) !important;
        animation: fadeInUp 0.8s ease-out backwards !important;
        transition: all 0.4s cubic-bezier(0.34, 1.56, 0.64, 1) !important;
    }

    [data-testid="stMetric"]:hover {
        transform: translateY(-8px) !important;
        box-shadow: 0 20px 50px rgba(99, 102, 241, 0.25), 
                    0 10px 30px rgba(0, 0, 0, 0.3) !important;
        border-color: rgba(99, 102, 241, 0.4) !important;
        background: rgba(15, 23, 42, 0.65) !important;
    }

    /* ═══════════════════════════════════════════════════════════════════════════ */
    /* COLUMNS & LAYOUT STYLING */
    /* ═══════════════════════════════════════════════════════════════════════════ */
    [data-testid="column"] {
        animation: fadeInUp 0.8s ease-out backwards !important;
    }

    /* ═══════════════════════════════════════════════════════════════════════════ */
    /* BUTTON STYLING WITH ANIMATIONS */
    /* ═══════════════════════════════════════════════════════════════════════════ */
    button[kind="primary"] {
        background: linear-gradient(135deg, #6366F1 0%, #7C3AED 100%) !important;
        color: #FFFFFF !important;
        border: 1px solid rgba(99, 102, 241, 0.3) !important;
        border-radius: 10px !important;
        padding: 12px 24px !important;
        font-weight: 600 !important;
        letter-spacing: 0.4px !important;
        box-shadow: 0 10px 25px rgba(99, 102, 241, 0.3) !important;
        transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1) !important;
        animation: fadeInUp 0.8s ease-out backwards !important;
    }

    button[kind="primary"]:hover {
        transform: translateY(-3px) !important;
        box-shadow: 0 15px 40px rgba(99, 102, 241, 0.5), 
                    0 0 20px rgba(99, 102, 241, 0.3) !important;
    }

    button[kind="primary"]:active {
        transform: translateY(-1px) !important;
    }

    button[kind="secondary"] {
        background: rgba(30, 41, 59, 0.6) !important;
        border: 1px solid rgba(148, 163, 184, 0.3) !important;
        color: #CBD5E1 !important;
        border-radius: 10px !important;
        transition: all 0.3s ease !important;
    }

    button[kind="secondary"]:hover {
        background: rgba(30, 41, 59, 0.9) !important;
        border-color: rgba(148, 163, 184, 0.6) !important;
        color: #F8FAFC !important;
    }

    /* ═══════════════════════════════════════════════════════════════════════════ */
    /* INPUT FIELDS STYLING */
    /* ═══════════════════════════════════════════════════════════════════════════ */
    input, textarea, select {
        background: rgba(30, 41, 59, 0.5) !important;
        border: 1px solid rgba(99, 102, 241, 0.2) !important;
        color: #F8FAFC !important;
        border-radius: 10px !important;
        padding: 10px 15px !important;
        transition: all 0.3s ease !important;
        font-family: 'Segoe UI', Roboto, sans-serif !important;
    }

    input:focus, textarea:focus, select:focus {
        background: rgba(30, 41, 59, 0.7) !important;
        border-color: rgba(99, 102, 241, 0.6) !important;
        box-shadow: 0 0 15px rgba(99, 102, 241, 0.2) !important;
        outline: none !important;
    }

    /* ═══════════════════════════════════════════════════════════════════════════ */
    /* SIDEBAR STYLING */
    /* ═══════════════════════════════════════════════════════════════════════════ */
    [data-testid="stSidebar"] {
        background: rgba(15, 23, 42, 0.7) !important;
        border-right: 1px solid rgba(99, 102, 241, 0.1) !important;
        backdrop-filter: blur(10px) !important;
    }

    [data-testid="stSidebarNav"] {
        animation: fadeInDown 1s ease-out !important;
    }

    /* ═══════════════════════════════════════════════════════════════════════════ */
    /* INFO, SUCCESS, WARNING, ERROR ALERTS */
    /* ═══════════════════════════════════════════════════════════════════════════ */
    .stAlert {
        background: rgba(15, 23, 42, 0.6) !important;
        border: 1px solid rgba(99, 102, 241, 0.2) !important;
        border-radius: 12px !important;
        backdrop-filter: blur(10px) !important;
        animation: fadeInUp 0.6s ease-out !important;
    }

    [data-testid="stAlertContainer"] > div {
        background: rgba(15, 23, 42, 0.6) !important;
        border: 1px solid rgba(99, 102, 241, 0.2) !important;
        border-radius: 12px !important;
        backdrop-filter: blur(10px) !important;
        padding: 16px !important;
    }

    /* ═══════════════════════════════════════════════════════════════════════════ */
    /* DATAFRAME STYLING */
    /* ═══════════════════════════════════════════════════════════════════════════ */
    [data-testid="stDataFrame"] {
        background: rgba(15, 23, 42, 0.5) !important;
        border-radius: 12px !important;
        overflow: hidden !important;
        animation: fadeInUp 0.8s ease-out !important;
    }

    [data-testid="stDataFrame"] > div {
        background: rgba(15, 23, 42, 0.5) !important;
    }

    /* ═══════════════════════════════════════════════════════════════════════════ */
    /* CHART STYLING */
    /* ═══════════════════════════════════════════════════════════════════════════ */
    [data-testid="stPlotlyChart"] {
        background: rgba(15, 23, 42, 0.5) !important;
        border: 1px solid rgba(99, 102, 241, 0.1) !important;
        border-radius: 12px !important;
        padding: 16px !important;
        backdrop-filter: blur(10px) !important;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2) !important;
        animation: fadeInUp 0.8s ease-out backwards !important;
    }

    /* ═══════════════════════════════════════════════════════════════════════════ */
    /* DIVIDER STYLING */
    /* ═══════════════════════════════════════════════════════════════════════════ */
    hr {
        border: none !important;
        height: 1px !important;
        background: linear-gradient(90deg, transparent, rgba(99, 102, 241, 0.3), transparent) !important;
        margin: 24px 0 !important;
    }

    /* ═══════════════════════════════════════════════════════════════════════════ */
    /* CUSTOM GLASSMORPHISM CARD CLASS */
    /* ═══════════════════════════════════════════════════════════════════════════ */
    .glass-card {
        background: rgba(15, 23, 42, 0.6) !important;
        backdrop-filter: blur(10px) !important;
        border: 1px solid rgba(99, 102, 241, 0.15) !important;
        border-radius: 16px !important;
        padding: 24px !important;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2) !important;
        animation: fadeInUp 0.8s ease-out backwards !important;
        transition: all 0.4s cubic-bezier(0.34, 1.56, 0.64, 1) !important;
    }

    .glass-card:hover {
        transform: translateY(-8px) !important;
        box-shadow: 0 20px 50px rgba(99, 102, 241, 0.25), 
                    0 10px 30px rgba(0, 0, 0, 0.3) !important;
        border-color: rgba(99, 102, 241, 0.4) !important;
        background: rgba(15, 23, 42, 0.7) !important;
    }

    /* NEON GREEN ACCENT CARD */
    .glass-card-accent-green {
        background: rgba(15, 23, 42, 0.6) !important;
        backdrop-filter: blur(10px) !important;
        border: 1px solid rgba(16, 185, 129, 0.15) !important;
        border-top: 2px solid rgba(16, 185, 129, 0.4) !important;
        border-radius: 16px !important;
        padding: 24px !important;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2) !important;
        animation: fadeInUp 0.8s ease-out backwards !important;
        transition: all 0.4s cubic-bezier(0.34, 1.56, 0.64, 1) !important;
    }

    .glass-card-accent-green:hover {
        transform: translateY(-8px) !important;
        box-shadow: 0 0 20px rgba(16, 185, 129, 0.3), 
                    0 20px 50px rgba(0, 0, 0, 0.3) !important;
        border-color: rgba(16, 185, 129, 0.4) !important;
    }

    /* ═══════════════════════════════════════════════════════════════════════════ */
    /* TEXT STYLING */
    /* ═══════════════════════════════════════════════════════════════════════════ */
    p {
        color: #CBD5E1 !important;
        line-height: 1.6 !important;
        font-family: 'Segoe UI', Roboto, sans-serif !important;
    }

    small {
        color: #94A3B8 !important;
        font-size: 13px !important;
    }

    /* ═══════════════════════════════════════════════════════════════════════════ */
    /* CODE BLOCK STYLING */
    /* ═══════════════════════════════════════════════════════════════════════════ */
    code {
        background: rgba(30, 41, 59, 0.6) !important;
        border: 1px solid rgba(99, 102, 241, 0.1) !important;
        color: #A5F3FC !important;
        border-radius: 6px !important;
        padding: 2px 6px !important;
    }

    [data-testid="stCodeBlock"] {
        background: rgba(15, 23, 42, 0.5) !important;
        border: 1px solid rgba(99, 102, 241, 0.1) !important;
        border-radius: 12px !important;
        animation: fadeInUp 0.8s ease-out !important;
    }

    /* ═══════════════════════════════════════════════════════════════════════════ */
    /* SMOOTH SCROLLBAR */
    /* ═══════════════════════════════════════════════════════════════════════════ */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }

    ::-webkit-scrollbar-track {
        background: rgba(15, 23, 42, 0.3);
    }

    ::-webkit-scrollbar-thumb {
        background: rgba(99, 102, 241, 0.4);
        border-radius: 4px;
    }

    ::-webkit-scrollbar-thumb:hover {
        background: rgba(99, 102, 241, 0.6);
    }

    /* ═══════════════════════════════════════════════════════════════════════════ */
    /* ANIMATION STAGGER FOR MULTIPLE ELEMENTS */
    /* ═══════════════════════════════════════════════════════════════════════════ */
    [data-testid="stMetric"]:nth-child(1) { animation-delay: 0s !important; }
    [data-testid="stMetric"]:nth-child(2) { animation-delay: 0.1s !important; }
    [data-testid="stMetric"]:nth-child(3) { animation-delay: 0.2s !important; }
    [data-testid="stMetric"]:nth-child(4) { animation-delay: 0.3s !important; }
    [data-testid="stMetric"]:nth-child(5) { animation-delay: 0.4s !important; }

</style>
"""

# ═══════════════════════════════════════════════════════════════════════════════
# INJECT ELITE CSS INTO STREAMLIT
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown(ELITE_CSS_ANIMATIONS, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Elite Business Analytics Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ═══════════════════════════════════════════════════════════════════════════════
# DATABASE INITIALIZATION & CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════
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

# ═══════════════════════════════════════════════════════════════════════════════
# CORE BUSINESS LOGIC (CONTROLLERS & ENGINES)
# ═══════════════════════════════════════════════════════════════════════════════
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
            if not sale:
                return False, "Record not found."
            session.delete(sale)
            session.commit()
            return True, "Record deleted successfully!"
        except Exception as e:
            session.rollback()
            return False, f"Error deleting record: {str(e)}"
        finally:
            session.close()

    @staticmethod
    def get_all_sales():
        session = get_db_session()
        try:
            sales = session.query(Sale).all()
            return sales
        finally:
            session.close()

class AnalyticsEngine:
    def __init__(self, session=get_db_session):
        self.session_factory = session

    def get_clean_dataframe(self):
        session = self.session_factory()
        try:
            sales = session.query(Sale).all()
            if not sales:
                return pd.DataFrame()
            
            data = [{
                'Sale ID': s.sale_id,
                'Product': s.product_name,
                'Category': s.category,
                'Quantity': s.quantity_sold,
                'Unit Price': float(s.unit_price),
                'Cost Price': float(s.cost_price),
                'Total Sales': float(s.total_sales),
                'Total Cost': float(s.total_cost),
                'Total Profit': float(s.total_profit),
                'Profit Margin %': float(s.profit_margin),
                'Sale Date': s.sale_date,
                'Region': s.region
            } for s in sales]
            
            return pd.DataFrame(data)
        finally:
            session.close()

    def generate_kpi_summary(self):
        df = self.get_clean_dataframe()
        
        if df.empty:
            return {
                'revenue': 0,
                'profit': 0,
                'orders': 0,
                'avg_ticket': 0,
                'top_product': 'N/A',
                'top_cat': 'N/A'
            }
        
        return {
            'revenue': df['Total Sales'].sum(),
            'profit': df['Total Profit'].sum(),
            'orders': len(df),
            'avg_ticket': df['Total Sales'].mean(),
            'top_product': df.loc[df['Total Profit'].idxmax(), 'Product'] if not df.empty else 'N/A',
            'top_cat': df['Category'].mode()[0] if not df['Category'].mode().empty else 'N/A'
        }

    def generate_ai_insights_dictionary(self):
        df = self.get_clean_dataframe()
        
        if df.empty:
            return {
                'revenue_trend': 'Insufficient data',
                'profit_trend': 'Insufficient data',
                'growth_trend': 'Insufficient data',
                'business_recommendations': 'Start entering sales data',
                'inventory_recommendations': 'Monitor inventory levels',
                'marketing_recommendations': 'Focus on high-margin products'
            }

        avg_margin = df['Profit Margin %'].mean()
        
        if avg_margin > 30:
            revenue_trend = "📈 Strong Positive Momentum"
            profit_trend = "📈 Excellent Profitability"
            growth_trend = "🚀 High Growth Potential"
        elif avg_margin > 15:
            revenue_trend = "📊 Steady Growth"
            profit_trend = "📊 Moderate Profitability"
            growth_trend = "📈 Consistent Expansion"
        else:
            revenue_trend = "⚠️ Needs Attention"
            profit_trend = "⚠️ Low Margins"
            growth_trend = "📉 Strategic Review Required"

        return {
            'revenue_trend': revenue_trend,
            'profit_trend': profit_trend,
            'growth_trend': growth_trend,
            'business_recommendations': f"Enhance product positioning for {avg_margin:.1f}% average margin optimization",
            'inventory_recommendations': f"Optimize stock levels based on {df['Category'].mode()[0]} category demand",
            'marketing_recommendations': f"Expand market presence in {df['Region'].mode()[0]} region"
        }

engine_instance = AnalyticsEngine()

# ═══════════════════════════════════════════════════════════════════════════════
# SIDEBAR NAVIGATION
# ═══════════════════════════════════════════════════════════════════════════════
st.sidebar.markdown("""
<div style="text-align: center; padding: 20px 0; animation: fadeInDown 0.8s ease-out;">
    <h2 style="color: #F8FAFC; font-size: 24px; margin: 0;">📊 Elite Analytics</h2>
    <p style="color: #94A3B8; font-size: 12px; letter-spacing: 0.5px; margin-top: 4px;">Business Intelligence Platform</p>
</div>
""", unsafe_allow_html=True)

st.sidebar.divider()

menu = st.sidebar.radio(
    "📍 Navigation Hub",
    ["🏠 Dashboard Overview", "➕ Add Sales Record", "📋 View & Manage Records", "📊 Advanced Analytics", "💡 AI-Driven Insights", "📁 Reports & File Exports", "⚙️ System Settings"],
    label_visibility="collapsed"
)

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: DASHBOARD OVERVIEW
# ═══════════════════════════════════════════════════════════════════════════════
if menu == "🏠 Dashboard Overview":
    st.title("Elite Business Analytics Dashboard")
    st.caption("Real-time performance metrics and intelligent business intelligence engine.")
    st.divider()
    
    metrics = engine_instance.generate_kpi_summary()
    
    # Display KPI Metrics with Animation
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="💰 Total Revenue",
            value=f"${metrics['revenue']:,.2f}",
            delta="Primary Income Stream"
        )
    
    with col2:
        st.metric(
            label="📈 Total Profit",
            value=f"${metrics['profit']:,.2f}",
            delta="Net Income Generated"
        )
    
    with col3:
        st.metric(
            label="📦 Total Orders",
            value=f"{metrics['orders']}",
            delta="Transaction Volume"
        )
    
    with col4:
        st.metric(
            label="🎯 Avg Order Value",
            value=f"${metrics['avg_ticket']:,.2f}",
            delta="Mean Transaction Amount"
        )
    
    st.divider()
    
    # Charts Section
    st.subheader("📊 Performance Analytics Matrix")
    
    df = engine_instance.get_clean_dataframe()
    
    if not df.empty:
        chart_col1, chart_col2 = st.columns(2)
        
        with chart_col1:
            st.markdown("### Revenue by Category")
            category_revenue = df.groupby('Category')['Total Sales'].sum().sort_values(ascending=False)
            
            fig_category = plt.figure(figsize=(10, 5), facecolor='rgba(15, 23, 42, 0.5)')
            ax = fig_category.add_subplot(111, facecolor='rgba(15, 23, 42, 0.5)')
            
            bars = ax.barh(category_revenue.index, category_revenue.values, color='#6366F1', edgecolor='#A5F3FC', linewidth=1.5)
            ax.set_xlabel('Revenue ($)', color='#94A3B8', fontsize=11)
            ax.set_title('Revenue Distribution', color='#F8FAFC', fontsize=12, fontweight='bold', pad=20)
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['left'].set_color('#94A3B8')
            ax.spines['bottom'].set_color('#94A3B8')
            ax.tick_params(colors='#94A3B8')
            
            plt.tight_layout()
            st.pyplot(fig_category)
        
        with chart_col2:
            st.markdown("### Profit Margin Trend")
            daily_margin = df.groupby('Sale Date')['Profit Margin %'].mean()
            
            fig_margin = plt.figure(figsize=(10, 5), facecolor='rgba(15, 23, 42, 0.5)')
            ax = fig_margin.add_subplot(111, facecolor='rgba(15, 23, 42, 0.5)')
            
            ax.plot(daily_margin.index, daily_margin.values, color='#10B981', linewidth=2.5, marker='o', markersize=6)
            ax.fill_between(daily_margin.index, daily_margin.values, alpha=0.2, color='#10B981')
            ax.set_xlabel('Date', color='#94A3B8', fontsize=11)
            ax.set_ylabel('Profit Margin (%)', color='#94A3B8', fontsize=11)
            ax.set_title('Profit Margin Trajectory', color='#F8FAFC', fontsize=12, fontweight='bold', pad=20)
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['left'].set_color('#94A3B8')
            ax.spines['bottom'].set_color('#94A3B8')
            ax.tick_params(colors='#94A3B8')
            plt.xticks(rotation=45, color='#94A3B8')
            
            plt.tight_layout()
            st.pyplot(fig_margin)
    else:
        st.info("📊 No data available yet. Add sales records to see analytics.")

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: ADD SALES RECORD
# ═══════════════════════════════════════════════════════════════════════════════
elif menu == "➕ Add Sales Record":
    st.title("Record Entry Engine")
    st.caption("Input new transactional sales data into the operational database.")
    st.divider()
    
    st.markdown("""
    <div class="glass-card">
        <h4>📝 New Sales Transaction Entry</h4>
        <p>Submit detailed sale information including product, pricing, and regional distribution metrics.</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.write("")
    
    col1, col2 = st.columns(2)
    
    with col1:
        product_name = st.text_input("Product Name", placeholder="Enter product name", key="product")
        category = st.selectbox("Product Category", ["Electronics", "Clothing", "Food", "Furniture", "Other"], key="category")
        quantity = st.number_input("Quantity Sold", min_value=1, key="quantity")
        unit_price = st.number_input("Unit Price ($)", min_value=0.01, format="%.2f", key="unit_price")
    
    with col2:
        cost_price = st.number_input("Cost Price ($)", min_value=0.01, format="%.2f", key="cost_price")
        sale_date = st.date_input("Sale Date", key="sale_date")
        region = st.selectbox("Region", ["North", "South", "East", "West", "Central"], key="region")
    
    st.divider()
    
    col_submit, col_clear = st.columns(2)
    
    with col_submit:
        if st.button("✅ Submit Record Entry", use_container_width=True, type="primary"):
            success, message = DataController.add_sale_record(
                product_name, category, quantity, unit_price, cost_price, sale_date, region
            )
            if success:
                st.success(f"✨ {message}")
                st.balloons()
            else:
                st.error(f"❌ {message}")
    
    with col_clear:
        if st.button("🔄 Reset Form", use_container_width=True):
            st.rerun()

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: VIEW & MANAGE RECORDS
# ═══════════════════════════════════════════════════════════════════════════════
elif menu == "📋 View & Manage Records":
    st.title("Records Management Interface")
    st.caption("Query, review, edit, and delete transactional sale records.")
    st.divider()
    
    df = engine_instance.get_clean_dataframe()
    
    if df.empty:
        st.warning("📭 No sales records found. Start by adding records in the 'Add Sales Record' section.")
    else:
        st.subheader(f"📊 Current Database: {len(df)} Active Records")
        
        # Display dataframe with custom styling
        st.markdown("""
        <style>
            .dataframe-container {
                background: rgba(15, 23, 42, 0.5);
                border-radius: 12px;
                overflow: hidden;
            }
        </style>
        """, unsafe_allow_html=True)
        
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        st.divider()
        st.subheader("🛠️ Record Modification Tools")
        
        action = st.radio("Select Operation:", ["Update Record", "Delete Record"], horizontal=True)
        
        if action == "Update Record":
            record_id = st.number_input("Enter Record ID to Update", min_value=1, key="update_id")
            
            sale = next((s for s in DataController.get_all_sales() if s.sale_id == record_id), None)
            
            if sale:
                st.success(f"✅ Record {record_id} found!")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    product_name = st.text_input("Product Name", value=sale.product_name, key="upd_product")
                    category = st.selectbox("Category", ["Electronics", "Clothing", "Food", "Furniture", "Other"], index=["Electronics", "Clothing", "Food", "Furniture", "Other"].index(sale.category), key="upd_category")
                    quantity = st.number_input("Quantity", value=sale.quantity_sold, key="upd_quantity")
                    unit_price = st.number_input("Unit Price", value=float(sale.unit_price), format="%.2f", key="upd_unit_price")
                
                with col2:
                    cost_price = st.number_input("Cost Price", value=float(sale.cost_price), format="%.2f", key="upd_cost_price")
                    sale_date = st.date_input("Sale Date", value=sale.sale_date, key="upd_date")
                    region = st.selectbox("Region", ["North", "South", "East", "West", "Central"], index=["North", "South", "East", "West", "Central"].index(sale.region), key="upd_region")
                
                if st.button("💾 Save Updates", use_container_width=True, type="primary"):
                    success, message = DataController.update_sale_record(record_id, product_name, category, quantity, unit_price, cost_price, sale_date, region)
                    if success:
                        st.success(f"✨ {message}")
                    else:
                        st.error(f"❌ {message}")
            else:
                st.error(f"❌ Record {record_id} not found.")
        
        else:  # Delete Record
            record_id = st.number_input("Enter Record ID to Delete", min_value=1, key="delete_id")
            
            if st.button("🗑️ Delete Record", use_container_width=True, type="primary"):
                success, message = DataController.delete_sale_record(record_id)
                if success:
                    st.success(f"✨ {message}")
                    st.rerun()
                else:
                    st.error(f"❌ {message}")

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: ADVANCED ANALYTICS
# ═══════════════════════════════════════════════════════════════════════════════
elif menu == "📊 Advanced Analytics":
    st.title("Advanced Analytics Engine")
    st.caption("Deep-dive statistical analysis with predictive modeling capabilities.")
    st.divider()
    
    df = engine_instance.get_clean_dataframe()
    
    if df.empty:
        st.warning("📊 No data available for analysis. Add sales records first.")
    else:
        tab1, tab2, tab3, tab4 = st.tabs(["Overview", "Category Analysis", "Regional Breakdown", "Predictive Trends"])
        
        with tab1:
            st.subheader("📈 Summary Statistics")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Records", len(df))
            with col2:
                st.metric("Avg Profit Margin", f"{df['Profit Margin %'].mean():.2f}%")
            with col3:
                st.metric("Date Range", f"{df['Sale Date'].min()} to {df['Sale Date'].max()}")
        
        with tab2:
            st.subheader("Category Performance Analysis")
            
            category_stats = df.groupby('Category').agg({
                'Total Sales': ['sum', 'mean'],
                'Total Profit': ['sum', 'mean'],
                'Quantity': 'sum',
                'Profit Margin %': 'mean'
            }).round(2)
            
            st.dataframe(category_stats, use_container_width=True)
        
        with tab3:
            st.subheader("Regional Market Distribution")
            
            region_stats = df.groupby('Region').agg({
                'Total Sales': 'sum',
                'Total Profit': 'sum',
                'Quantity': 'sum'
            }).sort_values('Total Sales', ascending=False)
            
            fig, ax = plt.subplots(figsize=(12, 5), facecolor='rgba(15, 23, 42, 0.5)')
            ax.bar(region_stats.index, region_stats['Total Sales'], color='#6366F1', edgecolor='#A5F3FC', linewidth=1.5, facecolor='rgba(99, 102, 241, 0.7)')
            ax.set_ylabel('Revenue ($)', color='#94A3B8')
            ax.set_title('Regional Revenue Distribution', color='#F8FAFC', fontweight='bold')
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['left'].set_color('#94A3B8')
            ax.spines['bottom'].set_color('#94A3B8')
            ax.tick_params(colors='#94A3B8')
            plt.tight_layout()
            st.pyplot(fig)
        
        with tab4:
            st.subheader("Predictive Trend Analysis")
            
            # Simple linear regression for trend
            df_sorted = df.sort_values('Sale Date').reset_index(drop=True)
            
            if len(df_sorted) > 2:
                X = np.arange(len(df_sorted)).reshape(-1, 1)
                y = df_sorted['Total Sales'].values
                
                model = LinearRegression()
                model.fit(X, y)
                y_pred = model.predict(X)
                
                fig, ax = plt.subplots(figsize=(12, 5), facecolor='rgba(15, 23, 42, 0.5)')
                ax.scatter(df_sorted.index, y, color='#10B981', s=100, alpha=0.6, label='Actual Sales')
                ax.plot(df_sorted.index, y_pred, color='#F59E0B', linewidth=2.5, label='Trend Line')
                ax.fill_between(df_sorted.index, y_pred, alpha=0.2, color='#F59E0B')
                ax.set_xlabel('Time Series Index', color='#94A3B8')
                ax.set_ylabel('Sales Value ($)', color='#94A3B8')
                ax.set_title('Sales Trend Prediction Model', color='#F8FAFC', fontweight='bold')
                ax.legend(facecolor='rgba(15, 23, 42, 0.5)', edgecolor='#94A3B8', labelcolor='#CBD5E1')
                ax.spines['top'].set_visible(False)
                ax.spines['right'].set_visible(False)
                ax.spines['left'].set_color('#94A3B8')
                ax.spines['bottom'].set_color('#94A3B8')
                ax.tick_params(colors='#94A3B8')
                plt.tight_layout()
                st.pyplot(fig)
            else:
                st.info("Need at least 3 data points for trend analysis.")

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: AI-DRIVEN INSIGHTS
# ═══════════════════════════════════════════════════════════════════════════════
elif menu == "💡 AI-Driven Insights":
    st.title("Intelligent Insights Engine")
    st.caption("AI-powered recommendations and strategic business intelligence.")
    st.divider()
    
    insights = engine_instance.generate_ai_insights_dictionary()
    
    sections = [
        ("📈 Systemic Revenue Trend Matrix Velocity", insights["revenue_trend"], "Gross transaction speed indicator."),
        ("📊 Systemic Capital Profit Margin Track", insights["profit_trend"], "Delta margin evaluation path."),
        ("🚀 Composite System Expansion Metrics", insights["growth_trend"], "General industrial strength evaluation framework."),
        ("💡 Strategic Corporate Business Execution Directive", insights["business_recommendations"], "Prescriptive administrative operations trajectory."),
        ("📦 Logistical Inventory Asset Optimization Allocation", insights["inventory_recommendations"], "Supply stream defensive holding instructions."),
        ("📣 Promotional Outreach Targeted Deployment Matrix", insights["marketing_recommendations"], "Geo-targeted public scaling framework configuration.")
    ]
    
    for i in range(0, len(sections), 2):
        col_left, col_right = st.columns(2)
        
        with col_left:
            title, desc, context = sections[i]
            st.markdown(f"""
            <div class="glass-card">
                <h4 style="color: #818CF8; margin-top:0; letter-spacing: 0.5px;">{title}</h4>
                <p style="font-size: 18px; font-weight: 700; margin: 12px 0; color: #F8FAFC;">{desc}</p>
                <small style="color: #94A3B8; font-style: italic;">Context: {context}</small>
            </div>
            """, unsafe_allow_html=True)
            
        if i + 1 < len(sections):
            with col_right:
                title, desc, context = sections[i+1]
                st.markdown(f"""
                <div class="glass-card-accent-green">
                    <h4 style="color: #34D399; margin-top:0; letter-spacing: 0.5px;">{title}</h4>
                    <p style="font-size: 18px; font-weight: 700; margin: 12px 0; color: #F8FAFC;">{desc}</p>
                    <small style="color: #94A3B8; font-style: italic;">Context: {context}</small>
                </div>
                """, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: REPORTS & FILE EXPORTS
# ═══════════════════════════════════════════════════════════════════════════════
elif menu == "📁 Reports & File Exports":
    st.title("Enterprise Financial Data Export Center")
    st.caption("Compile system variables into automated downstream ledgers and summaries.")
    st.divider()
    
    df = engine_instance.get_clean_dataframe()
    
    if df.empty:
        st.warning("There is no structural data to export yet.")
    else:
        st.markdown("### Select Target Export Channel:")
        
        st.markdown("""
        <div class="glass-card">
            <h4>📄 Flat Ledger Formats</h4>
        </div>
        """, unsafe_allow_html=True)
        
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Export Core Ledger to Flat File (CSV)",
            data=csv,
            file_name='enterprise_ledger.csv',
            mime='text/csv',
            use_container_width=True
        )
        
        st.write("")
        
        st.markdown("""
        <div class="glass-card">
            <h4>📈 Dynamic Workbook Sheets</h4>
        </div>
        """, unsafe_allow_html=True)
        
        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Ledger')
        st.download_button(
            label="📥 Compile Operational Sheet Workbooks (XLSX)",
            data=excel_buffer.getvalue(),
            file_name='enterprise_ledger.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            use_container_width=True
        )
        
        st.write("")
        
        st.markdown("""
        <div class="glass-card-accent-green">
            <h4>👑 High-Executive Summary Documents</h4>
        </div>
        """, unsafe_allow_html=True)
        
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
            label="📥 Generate AI Executive Core Document (PDF)",
            data=pdf_bytes,
            file_name="executive_summary.pdf",
            mime="application/pdf",
            use_container_width=True
        )

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: SYSTEM SETTINGS
# ═══════════════════════════════════════════════════════════════════════════════
elif menu == "⚙️ System Settings":
    st.title("Infrastructure Controls & Preferences")
    st.caption("Manage back-end schema specifications and database rollback systems.")
    st.divider()
    
    st.markdown("""
    <div class="glass-card">
        <h4>🎨 Visual Presentation Theme</h4>
        <p>Theme presentation frameworks (Dark/Light Canvas variants) are natively handled by Streamlit. Customize layouts directly inside Settings → Theme panels.</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.write("")
    
    st.markdown("""
    <div class="glass-card">
        <h4>⚙️ Data Core Architecture Specifications Matrix</h4>
    </div>
    """, unsafe_allow_html=True)
    
    st.code(f"Database Model Form: SQLite 3 relational local engine\nTarget Active Endpoint Mapping: {DB_FILE}\nTable Validation Index: Schema definitions verified.", language="yaml")
    
    st.write("")
    
    st.markdown("""
    <div class="glass-card-accent-green">
        <h4>💾 Administrative Disaster Recovery & Backup Pipelines</h4>
        <p>Ensure state preservation by downloading a direct physical backup copy of the SQLite runtime binary ledger.</p>
    </div>
    """, unsafe_allow_html=True)
    
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "rb") as file:
            st.download_button(
                label="💾 Download Raw Core Database Ledger (.db)",
                data=file,
                file_name="business_analytics_backup.db",
                mime="application/octet-stream",
                use_container_width=True
            )
    
    st.divider()
    
    st.markdown("""
    <div class="glass-card">
        <h4>🔄 Database Overwrite (Restore Pipeline)</h4>
    </div>
    """, unsafe_allow_html=True)
    
    st.warning("🚨 WARNING: Uploading a configuration file here completely rewrites and overwrites current data mappings.")
    
    uploaded_db = st.file_uploader("Upload .db Backup File Stream", type=["db"])
    if uploaded_db is not None:
        if st.button("🚨 Confirm Core Overwrite Sequence", type="primary", use_container_width=True):
            try:
                engine.dispose()
                with open(DB_FILE, "wb") as f:
                    f.write(uploaded_db.getbuffer())
                st.success("Database re-initialized from backup stream safely. Please refresh the page parameters.")
            except Exception as e:
                st.error(f"Database rewrite pipeline locked: {e}")

# ═══════════════════════════════════════════════════════════════════════════════
# FOOTER
# ═══════════════════════════════════════════════════════════════════════════════
st.divider()
st.markdown("""
<div style="text-align: center; padding: 20px; color: #94A3B8; font-size: 12px; animation: fadeInUp 0.8s ease-out 0.5s backwards;">
    <p>🚀 Elite Business Analytics Dashboard | Powered by Pure CSS Animations & Glassmorphism</p>
    <p style="margin-top: 8px; color: #64748B;">Zero Lag • 100% Streamlit Cloud Compatible • Professional Grade</p>
</div>
""", unsafe_allow_html=True)
