"""
DevScout Elite - Candidate Intelligence Dashboard
Real-time analytics and search interface for hiring decisions
"""
import os
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

try:
    import psycopg2
    HAS_DB = True
except ImportError:
    HAS_DB = False

st.set_page_config(
    page_title="DevScout Elite Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
    </style>
    """, unsafe_allow_html=True)


@st.cache_resource
def get_db_connection():
    """Create PostgreSQL connection."""
    if not HAS_DB:
        return None
    try:
        conn = psycopg2.connect(
            host=os.getenv('POSTGRES_HOST', 'postgres'),
            port=int(os.getenv('POSTGRES_PORT', 5432)),
            database=os.getenv('POSTGRES_DB', 'devscout_dw'),
            user=os.getenv('POSTGRES_USER', 'devscout'),
            password=os.getenv('POSTGRES_PASSWORD', 'devscout_pass')
        )
        return conn
    except Exception as e:
        st.error(f"Database connection failed: {e}")
        return None


@st.cache_data(ttl=60)
def fetch_candidate_summary(_conn):
    """Fetch candidate summary statistics."""
    if not _conn:
        return pd.DataFrame()
    query = """
        SELECT
            COUNT(DISTINCT c.candidate_id) as total_candidates,
            COUNT(DISTINCT c.education_level) as education_levels,
            AVG(c.years_experience) as avg_experience,
            COUNT(DISTINCT rs.skill_name) as total_skills,
            AVG(g.contribution_score) as avg_contribution
        FROM silver.candidates c
        LEFT JOIN silver.resume_skills rs ON c.candidate_id = rs.candidate_id
        LEFT JOIN silver.github_profiles g ON c.candidate_id = g.candidate_id;
    """
    try:
        return pd.read_sql(query, _conn)
    except Exception as e:
        st.error(f"Error fetching summary: {e}")
        _conn.rollback()
        return pd.DataFrame()


@st.cache_data(ttl=60)
def fetch_top_candidates(_conn, limit=20):
    """Fetch top-ranked candidates."""
    if not _conn:
        return pd.DataFrame()
    query = f"""
        SELECT
            r.ranking_position,
            r.candidate_name,
            dc.email,
            dc.years_experience,
            dc.education_level,
            r.total_score,
            r.percentile,
            sc.github_username,
            g.total_repos,
            g.total_stars,
            g.primary_language
        FROM gold.agg_candidate_rankings r
        JOIN gold.dim_candidates dc ON r.candidate_key = dc.candidate_key
        LEFT JOIN silver.candidates sc ON dc.candidate_id = sc.candidate_id
        LEFT JOIN silver.github_profiles g ON dc.candidate_id = g.candidate_id
        ORDER BY r.ranking_position
        LIMIT {limit};
    """
    try:
        return pd.read_sql(query, _conn)
    except Exception as e:
        st.error(f"Error fetching candidates: {e}")
        _conn.rollback()
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
        return pd.read_sql(query, _conn)
    except Exception as e:
        st.error(f"Error fetching skills: {e}")
        _conn.rollback()
        return pd.DataFrame()


@st.cache_data(ttl=60)
def fetch_pipeline_metrics(_conn):
    """Fetch pipeline execution metrics."""
    if not _conn:
        return pd.DataFrame()
    query = """
        SELECT
            pipeline_name,
            status,
            records_processed,
            run_date,
            started_at,
            completed_at,
            EXTRACT(EPOCH FROM (completed_at - started_at)) as duration_seconds
        FROM metadata.pipeline_runs
        WHERE run_date >= CURRENT_DATE - INTERVAL '7 days'
        ORDER BY run_date DESC
        LIMIT 50;
    """
    try:
        return pd.read_sql(query, _conn)
    except Exception as e:
        st.error(f"Error fetching pipeline metrics: {e}")
        _conn.rollback()
        return pd.DataFrame()


# Sidebar
st.sidebar.title("DevScout Elite")
st.sidebar.markdown("---")

page = st.sidebar.radio(
    "Navigate",
    ["Dashboard", "Candidate Search", "Pipeline Monitoring", "Analytics"]
)

st.sidebar.markdown("---")
st.sidebar.info(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

conn = get_db_connection()

if page == "Dashboard":
    st.title("DevScout Elite Dashboard")
    st.markdown("Real-time hiring intelligence platform")

    summary_df = fetch_candidate_summary(conn)

    if not summary_df.empty:
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "Total Candidates",
                f"{int(summary_df['total_candidates'].iloc[0]):,}"
            )
        with col2:
            st.metric(
                "Avg Experience",
                f"{summary_df['avg_experience'].iloc[0]:.1f} years"
            )
        with col3:
            st.metric(
                "Unique Skills",
                f"{int(summary_df['total_skills'].iloc[0]):,}"
            )
        with col4:
            avg_contrib = summary_df['avg_contribution'].iloc[0]
            if avg_contrib and pd.notna(avg_contrib):
                st.metric("Avg Contribution Score", f"{avg_contrib:.1f}")
            else:
                st.metric("Avg Contribution Score", "N/A")

    st.markdown("---")

    st.subheader("Top Candidates")
    candidates_df = fetch_top_candidates(conn, limit=20)

    if not candidates_df.empty:
        display_df = candidates_df[[
            'ranking_position', 'candidate_name', 'years_experience',
            'education_level', 'total_score', 'github_username'
        ]].copy()
        display_df.columns = ['Rank', 'Name', 'Experience', 'Education', 'Score', 'GitHub']

        st.dataframe(display_df, use_container_width=True, hide_index=True)
    else:
        st.info("No candidate data available yet. Start the pipelines to load data.")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Top Skills Distribution")
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
        st.subheader("Score Distribution")
        if not candidates_df.empty:
            fig = px.histogram(
                candidates_df,
                x='total_score',
                nbins=20,
                labels={'total_score': 'Total Score'},
                title='Candidate Score Distribution'
            )
            fig.update_layout(showlegend=False, height=400)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No score data available")

elif page == "Candidate Search":
    st.title("Candidate Search")
    st.markdown("Find candidates by skill or name")

    search_query = st.text_input(
        "Enter your search query",
        placeholder="e.g., Python, React, machine learning"
    )

    col1, col2 = st.columns([1, 4])
    with col1:
        max_results = st.number_input("Max Results", min_value=5, max_value=50, value=10)
    with col2:
        search_button = st.button("Search", type="primary")

    if search_button and search_query:
        with st.spinner("Searching candidates..."):
            if conn:
                query = """
                    SELECT DISTINCT
                        dc.full_name,
                        dc.email,
                        dc.years_experience,
                        dc.education_level,
                        ARRAY_AGG(DISTINCT rs.skill_name) as skills,
                        sc.github_username,
                        g.total_repos,
                        r.total_score
                    FROM gold.dim_candidates dc
                    LEFT JOIN silver.resume_skills rs ON dc.candidate_id = rs.candidate_id
                    LEFT JOIN silver.candidates sc ON dc.candidate_id = sc.candidate_id
                    LEFT JOIN silver.github_profiles g ON dc.candidate_id = g.candidate_id
                    LEFT JOIN gold.agg_candidate_rankings r ON dc.candidate_key = r.candidate_key
                    WHERE dc.full_name ILIKE %s
                       OR rs.skill_name ILIKE %s
                    GROUP BY dc.candidate_key, dc.full_name, dc.email,
                             dc.years_experience, dc.education_level,
                             sc.github_username, g.total_repos, r.total_score
                    ORDER BY r.total_score DESC NULLS LAST
                    LIMIT %s;
                """
                try:
                    search_param = f"%{search_query}%"
                    results_df = pd.read_sql(query, conn, params=(search_param, search_param, max_results))

                    if not results_df.empty:
                        st.success(f"Found {len(results_df)} matching candidates")
                        for idx, row in results_df.iterrows():
                            score = row['total_score'] if row['total_score'] else 0
                            with st.expander(f"{row['full_name']} (Score: {score})"):
                                c1, c2 = st.columns([2, 1])
                                with c1:
                                    st.write(f"**Email:** {row['email']}")
                                    st.write(f"**Experience:** {row['years_experience']} years")
                                    st.write(f"**Education:** {row['education_level']}")
                                    skills_list = row['skills'] if row['skills'] else []
                                    st.write(f"**Skills:** {', '.join(skills_list[:10]) if skills_list else 'N/A'}")
                                with c2:
                                    if row['github_username']:
                                        st.write(f"**GitHub:** {row['github_username']}")
                                        st.write(f"**Repos:** {row['total_repos']}")
                                    st.metric("Total Score", f"{score}")
                    else:
                        st.warning("No candidates found matching your query.")
                except Exception as e:
                    st.error(f"Search error: {e}")
                    conn.rollback()
            else:
                st.error("Database connection not available")

elif page == "Pipeline Monitoring":
    st.title("Pipeline Monitoring")
    st.markdown("Monitor data pipeline execution and health")

    metrics_df = fetch_pipeline_metrics(conn)

    if not metrics_df.empty:
        col1, col2, col3 = st.columns(3)

        total_runs = len(metrics_df)
        successful_runs = len(metrics_df[metrics_df['status'] == 'success'])
        success_rate = (successful_runs / total_runs) * 100 if total_runs > 0 else 0

        with col1:
            st.metric("Total Runs (7d)", total_runs)
        with col2:
            st.metric("Success Rate", f"{success_rate:.1f}%")
        with col3:
            avg_time = metrics_df['duration_seconds'].mean()
            st.metric("Avg Duration", f"{avg_time:.1f}s" if pd.notna(avg_time) else "N/A")

        st.markdown("---")
        st.subheader("Recent Pipeline Runs")

        display_metrics = metrics_df[[
            'pipeline_name', 'status', 'records_processed',
            'duration_seconds', 'run_date'
        ]].copy()

        st.dataframe(display_metrics, use_container_width=True, hide_index=True)

        st.subheader("Pipeline Execution Timeline")
        fig = px.scatter(
            metrics_df,
            x='run_date',
            y='pipeline_name',
            color='status',
            size='duration_seconds',
            hover_data=['records_processed'],
            title='Pipeline Runs Over Time'
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No pipeline metrics available yet.")

elif page == "Analytics":
    st.title("Advanced Analytics")
    st.markdown("Deep dive into candidate trends and insights")

    candidates_df = fetch_top_candidates(conn, limit=100)

    if not candidates_df.empty:
        st.subheader("Experience vs Performance")
        fig = px.scatter(
            candidates_df,
            x='years_experience',
            y='total_score',
            color='education_level',
            hover_data=['candidate_name'],
            labels={
                'years_experience': 'Years of Experience',
                'total_score': 'Total Score'
            },
            title='Experience vs Total Score'
        )
        st.plotly_chart(fig, use_container_width=True)

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("GitHub Activity")
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
            st.subheader("Language Distribution")
            if not github_df.empty and 'primary_language' in github_df.columns:
                lang_counts = github_df['primary_language'].value_counts().head(10)
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

st.markdown("---")
st.markdown(
    """
    <div style='text-align: center'>
        <p>DevScout Elite Platform | Built with Streamlit, PostgreSQL & Weaviate</p>
        <p><small>Data refreshes every 60 seconds</small></p>
    </div>
    """,
    unsafe_allow_html=True
)
