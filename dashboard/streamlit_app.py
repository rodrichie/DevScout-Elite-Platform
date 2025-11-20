"""
DevScout Elite - Candidate Intelligence Dashboard
Real-time analytics and search interface for hiring decisions
"""
import os
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    HAS_DB = True
except ImportError:
    HAS_DB = False
    st.error(" psycopg2 not installed. Database features disabled.")

try:
    from weaviate import Client
    HAS_WEAVIATE = True
except ImportError:
    HAS_WEAVIATE = False
    st.warning(" Weaviate client not installed. Vector search disabled.")


# Page config
st.set_page_config(
    page_title="DevScout Elite Dashboard",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .big-font {
        font-size:20px !important;
        font-weight: bold;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
    </style>
    """, unsafe_allow_html=True)


# Database connection
@st.cache_resource
def get_db_connection():
    """Create PostgreSQL connection."""
    if not HAS_DB:
        return None
    
    try:
        conn = psycopg2.connect(
            host=os.getenv('POSTGRES_HOST', 'postgres'),
            port=int(os.getenv('POSTGRES_PORT', 5432)),
            database=os.getenv('POSTGRES_DB', 'devscout'),
            user=os.getenv('POSTGRES_USER', 'airflow'),
            password=os.getenv('POSTGRES_PASSWORD', 'airflow')
        )
        return conn
    except Exception as e:
        st.error(f"Database connection failed: {e}")
        return None


# Weaviate connection
@st.cache_resource
def get_weaviate_client():
    """Create Weaviate client."""
    if not HAS_WEAVIATE:
        return None
    
    try:
        client = Client(
            url=os.getenv('WEAVIATE_URL', 'http://weaviate:8080')
        )
        return client
    except Exception as e:
        st.warning(f"Weaviate connection failed: {e}")
        return None


# Data fetching functions
@st.cache_data(ttl=60)
def fetch_candidate_summary(_conn):
    """Fetch candidate summary statistics."""
    if not _conn:
        return pd.DataFrame()
    
    query = """
        SELECT 
            COUNT(*) as total_candidates,
            COUNT(DISTINCT c.education_level) as education_levels,
            AVG(c.years_experience) as avg_experience,
            COUNT(DISTINCT rs.skill_name) as total_skills,
            AVG(g.code_quality_score) as avg_code_quality,
            AVG(g.contribution_score) as avg_contribution
        FROM silver.candidates c
        LEFT JOIN silver.resume_skills rs ON c.candidate_id = rs.candidate_id
        LEFT JOIN silver.github_profiles g ON c.candidate_id = g.candidate_id;
    """
    
    try:
        df = pd.read_sql(query, _conn)
        return df
    except Exception as e:
        st.error(f"Error fetching summary: {e}")
        return pd.DataFrame()


@st.cache_data(ttl=60)
def fetch_top_candidates(_conn, limit=20):
    """Fetch top-ranked candidates."""
    if not _conn:
        return pd.DataFrame()
    
    query = f"""
        SELECT 
            cr.rank,
            c.candidate_name,
            c.email,
            c.years_experience,
            c.education_level,
            cr.overall_score,
            cr.technical_score,
            cr.github_score,
            g.github_username,
            g.total_repos,
            g.total_stars,
            g.top_language
        FROM gold.agg_candidate_rankings cr
        JOIN gold.dim_candidates c ON cr.candidate_id = c.candidate_id
        LEFT JOIN silver.github_profiles g ON cr.candidate_id = g.candidate_id
        ORDER BY cr.rank
        LIMIT {limit};
    """
    
    try:
        df = pd.read_sql(query, _conn)
        return df
    except Exception as e:
        st.error(f"Error fetching candidates: {e}")
        return pd.DataFrame()


@st.cache_data(ttl=60)
def fetch_skill_distribution(_conn, top_n=15):
    """Fetch top skills distribution."""
    if not _conn:
        return pd.DataFrame()
    
    query = f"""
        SELECT 
            skill_name,
            COUNT(DISTINCT candidate_id) as candidate_count,
            skill_category
        FROM silver.resume_skills
        GROUP BY skill_name, skill_category
        ORDER BY candidate_count DESC
        LIMIT {top_n};
    """
    
    try:
        df = pd.read_sql(query, _conn)
        return df
    except Exception as e:
        st.error(f"Error fetching skills: {e}")
        return pd.DataFrame()


@st.cache_data(ttl=60)
def fetch_pipeline_metrics(_conn):
    """Fetch pipeline execution metrics."""
    if not _conn:
        return pd.DataFrame()
    
    query = """
        SELECT 
            pipeline_name,
            run_status,
            records_processed,
            records_failed,
            execution_time_seconds,
            run_date
        FROM metadata.pipeline_runs
        WHERE run_date >= CURRENT_DATE - INTERVAL '7 days'
        ORDER BY run_date DESC
        LIMIT 50;
    """
    
    try:
        df = pd.read_sql(query, _conn)
        return df
    except Exception as e:
        st.error(f"Error fetching pipeline metrics: {e}")
        return pd.DataFrame()


# Sidebar
st.sidebar.title(" DevScout Elite")
st.sidebar.markdown("---")

page = st.sidebar.radio(
    "Navigate",
    [" Dashboard", " Candidate Search", " Pipeline Monitoring", " Analytics"]
)

st.sidebar.markdown("---")
st.sidebar.info(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# Get database connection
conn = get_db_connection()

# Main content
if page == " Dashboard":
    st.title(" DevScout Elite Dashboard")
    st.markdown("Real-time hiring intelligence platform")
    
    # Summary metrics
    summary_df = fetch_candidate_summary(conn)
    
    if not summary_df.empty:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Total Candidates",
                f"{int(summary_df['total_candidates'].iloc[0]):,}",
                delta="+12 this week"
            )
        
        with col2:
            st.metric(
                "Avg Experience",
                f"{summary_df['avg_experience'].iloc[0]:.1f} years",
                delta="+0.5 yrs"
            )
        
        with col3:
            st.metric(
                "Unique Skills",
                f"{int(summary_df['total_skills'].iloc[0]):,}",
                delta="+28"
            )
        
        with col4:
            avg_score = summary_df['avg_code_quality'].iloc[0]
            st.metric(
                "Avg Code Quality",
                f"{avg_score:.1f}/100",
                delta=f"+{2.3:.1f}"
            )
    
    st.markdown("---")
    
    # Top Candidates Table
    st.subheader(" Top Candidates")
    
    candidates_df = fetch_top_candidates(conn, limit=20)
    
    if not candidates_df.empty:
        # Format for display
        display_df = candidates_df[[
            'rank', 'candidate_name', 'years_experience', 
            'education_level', 'overall_score', 'github_username'
        ]].copy()
        
        display_df.columns = ['Rank', 'Name', 'Experience', 'Education', 'Score', 'GitHub']
        
        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No candidate data available yet. Start the pipelines to load data.")
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader(" Top Skills Distribution")
        skills_df = fetch_skill_distribution(conn, top_n=10)
        
        if not skills_df.empty:
            fig = px.bar(
                skills_df,
                x='candidate_count',
                y='skill_name',
                orientation='h',
                color='skill_category',
                labels={'candidate_count': 'Candidates', 'skill_name': 'Skill'},
                title='Most In-Demand Skills'
            )
            fig.update_layout(showlegend=True, height=400)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No skill data available")
    
    with col2:
        st.subheader(" Score Distribution")
        
        if not candidates_df.empty:
            fig = px.histogram(
                candidates_df,
                x='overall_score',
                nbins=20,
                labels={'overall_score': 'Overall Score'},
                title='Candidate Score Distribution'
            )
            fig.update_layout(showlegend=False, height=400)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No score data available")

elif page == " Candidate Search":
    st.title(" Semantic Candidate Search")
    st.markdown("Find candidates using natural language queries")
    
    # Search interface
    search_query = st.text_input(
        "Enter your search query",
        placeholder="e.g., Python developer with 5+ years in data engineering and AWS"
    )
    
    col1, col2 = st.columns([1, 4])
    
    with col1:
        max_results = st.number_input("Max Results", min_value=5, max_value=50, value=10)
    
    with col2:
        search_button = st.button(" Search", type="primary")
    
    if search_button and search_query:
        with st.spinner("Searching candidates..."):
            # TODO: Implement Weaviate vector search
            st.info("Vector search will be implemented when Weaviate is configured.")
            
            # Fallback: SQL search
            if conn:
                query = f"""
                    SELECT 
                        c.candidate_name,
                        c.email,
                        c.years_experience,
                        c.education_level,
                        ARRAY_AGG(DISTINCT rs.skill_name) as skills,
                        g.github_username,
                        g.total_repos,
                        cr.overall_score
                    FROM silver.candidates c
                    LEFT JOIN silver.resume_skills rs ON c.candidate_id = rs.candidate_id
                    LEFT JOIN silver.github_profiles g ON c.candidate_id = g.candidate_id
                    LEFT JOIN gold.agg_candidate_rankings cr ON c.candidate_id = cr.candidate_id
                    WHERE c.resume_text ILIKE '%{search_query}%'
                       OR rs.skill_name ILIKE '%{search_query}%'
                    GROUP BY c.candidate_id, g.github_username, g.total_repos, cr.overall_score
                    LIMIT {max_results};
                """
                
                try:
                    results_df = pd.read_sql(query, conn)
                    
                    if not results_df.empty:
                        st.success(f"Found {len(results_df)} matching candidates")
                        
                        for idx, row in results_df.iterrows():
                            with st.expander(f" {row['candidate_name']} (Score: {row['overall_score']:.1f})"):
                                col1, col2 = st.columns([2, 1])
                                
                                with col1:
                                    st.write(f"**Email:** {row['email']}")
                                    st.write(f"**Experience:** {row['years_experience']} years")
                                    st.write(f"**Education:** {row['education_level']}")
                                    st.write(f"**Skills:** {', '.join(row['skills'][:10]) if row['skills'] else 'N/A'}")
                                
                                with col2:
                                    if row['github_username']:
                                        st.write(f"**GitHub:** [@{row['github_username']}](https://github.com/{row['github_username']})")
                                        st.write(f"**Repos:** {row['total_repos']}")
                                    
                                    st.metric("Overall Score", f"{row['overall_score']:.1f}/100")
                    else:
                        st.warning("No candidates found matching your query.")
                
                except Exception as e:
                    st.error(f"Search error: {e}")
            else:
                st.error("Database connection not available")

elif page == " Pipeline Monitoring":
    st.title(" Pipeline Monitoring")
    st.markdown("Monitor data pipeline execution and health")
    
    # Pipeline metrics
    metrics_df = fetch_pipeline_metrics(conn)
    
    if not metrics_df.empty:
        # Success rate
        col1, col2, col3 = st.columns(3)
        
        total_runs = len(metrics_df)
        successful_runs = len(metrics_df[metrics_df['run_status'] == 'success'])
        success_rate = (successful_runs / total_runs) * 100
        
        with col1:
            st.metric("Total Runs (7d)", total_runs)
        
        with col2:
            st.metric("Success Rate", f"{success_rate:.1f}%")
        
        with col3:
            avg_time = metrics_df['execution_time_seconds'].mean()
            st.metric("Avg Execution Time", f"{avg_time:.1f}s")
        
        st.markdown("---")
        
        # Pipeline status table
        st.subheader("Recent Pipeline Runs")
        
        display_metrics = metrics_df[[
            'pipeline_name', 'run_status', 'records_processed', 
            'records_failed', 'execution_time_seconds', 'run_date'
        ]].copy()
        
        # Color code status
        def color_status(val):
            color = 'green' if val == 'success' else ('red' if val == 'failed' else 'orange')
            return f'background-color: {color}; color: white'
        
        st.dataframe(
            display_metrics.style.applymap(color_status, subset=['run_status']),
            use_container_width=True
        )
        
        # Timeline chart
        st.subheader(" Pipeline Execution Timeline")
        
        fig = px.scatter(
            metrics_df,
            x='run_date',
            y='pipeline_name',
            color='run_status',
            size='execution_time_seconds',
            hover_data=['records_processed', 'records_failed'],
            title='Pipeline Runs Over Time'
        )
        st.plotly_chart(fig, use_container_width=True)
        
    else:
        st.info("No pipeline metrics available yet.")

elif page == " Analytics":
    st.title(" Advanced Analytics")
    st.markdown("Deep dive into candidate trends and insights")
    
    candidates_df = fetch_top_candidates(conn, limit=100)
    
    if not candidates_df.empty:
        # Experience vs Score
        st.subheader(" Experience vs Performance")
        
        fig = px.scatter(
            candidates_df,
            x='years_experience',
            y='overall_score',
            color='education_level',
            size='github_score',
            hover_data=['candidate_name'],
            labels={
                'years_experience': 'Years of Experience',
                'overall_score': 'Overall Score'
            },
            title='Experience vs Overall Score'
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # GitHub stats
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader(" GitHub Activity")
            
            github_df = candidates_df[candidates_df['github_username'].notna()]
            
            if not github_df.empty:
                fig = px.bar(
                    github_df.head(15),
                    x='candidate_name',
                    y='total_stars',
                    color='total_repos',
                    labels={'total_stars': 'Stars', 'candidate_name': 'Candidate'},
                    title='Top Contributors by Stars'
                )
                fig.update_xaxis(tickangle=-45)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No GitHub data available")
        
        with col2:
            st.subheader(" Language Distribution")
            
            if not github_df.empty and 'top_language' in github_df.columns:
                lang_counts = github_df['top_language'].value_counts().head(10)
                
                fig = px.pie(
                    values=lang_counts.values,
                    names=lang_counts.index,
                    title='Primary Languages'
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No language data available")
    else:
        st.info("No analytics data available yet.")

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center'>
        <p> DevScout Elite Platform | Built with Streamlit, PostgreSQL & Weaviate</p>
        <p><small>Data refreshes every 60 seconds</small></p>
    </div>
    """,
    unsafe_allow_html=True
)
