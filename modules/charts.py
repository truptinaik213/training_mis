import plotly.express as px
import plotly.graph_objects as go


def topic_distribution_chart(df):
    fig = px.bar(
        df,
        x="category",
        y="participants",
        title="Confirmed Participants by Category",
        text="participants"
    )

    fig.update_layout(
        xaxis_title="Category",
        yaxis_title="Confirmed Participants",
        template="plotly_white",
        showlegend=False
    )

    return fig


def topic_popularity_chart(df):
    """Lollipop chart — top training topics by confirmed participants.

    FIX: shapes now reference category strings on the y-axis instead of
    integer indices.  When a Scatter trace uses a string column for y,
    Plotly creates a *categorical* y-axis.  Shape coordinates on a
    categorical axis must also be strings (the category values), not
    integers — integer coordinates are treated as numeric and therefore
    land on the wrong row.
    """
    fig = go.Figure()

    for row in df.itertuples():
        fig.add_shape(
            type="line",
            x0=0,
            x1=row.participants,
            # FIX: use the actual topic string, not the integer loop index
            y0=row.training_topic,
            y1=row.training_topic,
            line=dict(color="steelblue", width=2),
        )

    fig.add_trace(
        go.Scatter(
            x=df["participants"],
            y=df["training_topic"],
            mode="markers",
            marker=dict(size=12, color="steelblue"),
            name="Participants",
        )
    )

    fig.update_layout(
        title="Top Training Topics",
        xaxis_title="Confirmed Participants",
        yaxis_title="Training Topic",
        template="plotly_white",
        # Keep the descending order returned by the query
        yaxis=dict(categoryorder="array", categoryarray=df["training_topic"].tolist()),
    )

    return fig


def attendance_trend_chart(df):
    fig = px.line(
        df,
        x="month",
        y="avg_attendance",
        markers=True,
        title="Attendance Trend"
    )

    fig.update_layout(
        xaxis_title="Month",
        yaxis_title="Average Attendance %",
        template="plotly_white"
    )

    return fig


def training_type_donut(df):
    fig = px.pie(
        df,
        names="training_type",
        values="trainings",
        hole=0.55,
        title="Training Type Distribution"
    )

    fig.update_layout(
        template="plotly_white"
    )

    return fig


def mode_category_chart(df):
    temp = df.copy()

    temp["percentage"] = (
        temp["trainings"]
        / temp.groupby("category")["trainings"].transform("sum")
    ) * 100

    fig = px.bar(
        temp,
        x="category",
        y="percentage",
        color="mode",
        barmode="stack",
        title="Training Mode by Category (%)"
    )

    fig.update_layout(
        xaxis_title="Category",
        yaxis_title="Percentage",
        template="plotly_white"
    )

    return fig


def calculate_conversion_rate(nominations, confirmed):
    if nominations == 0:
        return 0
    return round((confirmed / nominations) * 100, 2)
