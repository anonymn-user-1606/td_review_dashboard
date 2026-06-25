# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "altair==6.2.1",
#     "google-api-python-client==2.194.0",
#     "google-auth-oauthlib==1.3.1",
#     "gspread==6.2.1",
#     "gspread-dataframe==4.0.0",
#     "marimo",
#     "networkx==3.6.1",
#     "openpyxl==3.1.5",
#     "pandas==3.0.2",
#     "pyarrow==24.0.0",
#     "pybliometrics==4.4.1",
#     "requests==2.33.1",
#     "tqdm==4.67.3",
#     "xlsxwriter==3.2.9",
# ]
# ///

import marimo

__generated_with = "0.23.10"
app = marimo.App(width="full")


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # TD Review - Citation Network Analysis Dashboard <br>
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    This dashboard is part of the supplemental material. The purpose of this dashboard is to offer interactivity to the readers so they understand better the citation network of the sample of TD review as static images on a article renders limited understanding
    """)
    return


@app.cell
def importing_libraries():
    # importing libraries
    import marimo as mo
    import pandas as pd
    import pickle
    import networkx as nx
    import numpy as np
    import altair as alt

    return alt, mo, nx, pd


@app.cell(hide_code=True)
def data_loading(pd):
    #fetching the data from excel table
    #raw_df2 = pd.read_excel("dat2.xlsx")

    sheet_id = "1HZD3-9_xvM74g7C_fQ5LdDM6OtU00fjwRdwL6zTXdM8"
    sheet_name = "data"

    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={sheet_name}"

    raw_df2 = pd.read_csv(url)


    #creating a new column "research approach"
    raw_df2.loc[raw_df2["TD"]==1, "research_approach"]  = "TD"
    raw_df2.loc[raw_df2["LRW"]==1, "research_approach"]  = "LWR"

    cols = ["TD-URBAN", "TD-RURAL", "TD-OTHER", "LRW-URBAN", "LRW-RURAL", "LRW-OTHER"]

    id_cols = [c for c in raw_df2.columns if c not in cols]
    raw_df2 = (
        raw_df2.melt(
            id_vars=id_cols,
            value_vars=cols,
            var_name="urban/rural",
            value_name="_flag"
        )
        .query("_flag == 1")        # ← keep only the active category
        .drop(columns="_flag")
        .reset_index(drop=True)
    )

    columns_to_keep2 = ["N°", "EID","Title", "Year", "Authors", "Cited by", "cluster_number", "research_approach", "urban/rural"]

    #Creating fresher version of the dataframe
    df2 = raw_df2.copy()[columns_to_keep2]
    df2["scopus_id"] = df2["EID"].str.split("-s2.0-").str[-1] 

    df2["cluster_number"] = df2["cluster_number"].astype(str)
    df2["cluster_number"] = df2["cluster_number"].str[:-2]
    df2.loc[df2["cluster_number"].isna(), "cluster_number"] = "no cluster assigned"
    df2["Year"] = df2["Year"].astype(str)

    #Getting the eids into a list
    eids2 = df2["EID"].tolist()
    df=df2


    sheet_name2 = "references_df"

    url2 = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={sheet_name2}"

    ref_df = pd.read_csv(url2)
    ref_df["scopus_id"] = ref_df["scopus_id"].astype(str)
    return df, ref_df


@app.cell
def _(df, mo):
    cluster_options = sorted(df["cluster_number"].unique().tolist())
    cluster_options.append("all")
    cluster_options.remove("no cluster assigned")

    selector = mo.ui.radio(
        options=cluster_options,
        label="Select a cluster option",
        value="all",
        inline=True
    )
    return (selector,)


@app.cell
def _(df_change, ref_df):
    scopus_ids = df_change["scopus_id"].unique().tolist()
    references_df = ref_df.copy().loc[ref_df["scopus_id"].isin(scopus_ids),]
    return (references_df,)


@app.cell(hide_code=True)
def pickle_loading():
    #saving it into a pickle
    #with open('pickles/articles_raw_list.pkl', 'wb') as file:
    #    articles_ = pickle.dump(articles, file)

    #with open('pickles/articles_raw_list.pkl', 'rb') as file:
    #    articles = pickle.load(file)
    return


@app.cell(hide_code=True)
def reference_df_creation():

    #ids = []
    #refs = []
    #titles = []
    #autores = []
    #años = []

    #for j in range(len(articles)):
    #    if articles[j].references is not None:
    #        for art in articles[j].references:
    #            ids.append(str(articles[j].identifier))
    #            refs.append(art.id)
    #            titles.append(art.title)
    #            autores.append(art.authors)
    #            años.append(art.publicationyear)
    #    else:
    #        ids.append(str(articles[j].identifier))
    #        refs.append("no references in metadata")
    #        titles.append("no references in metadata")
     #       autores.append("no references in metadata")
     #       años.append("no references in metadata")

    #references_dict = {
    #    "scopus_id": ids,
    #    "cite_to": refs,
    #    "title": titles,
    #    "author": autores,
    #    "year": años
    #}

    #references_df = pd.DataFrame(references_dict)
    return


@app.cell(hide_code=True)
def top_10_cited_df(pd, references_df):
    #getting only the top 10 most cited articles in the sample
    top_cited = (
                    references_df.groupby("cite_to")
                                 .count()["scopus_id"]
                                 .sort_values(ascending=False)
                                 .reset_index(drop=False).head(10)
    )
    top_cited = top_cited.rename(columns={"scopus_id":"citations_count"})

    top10_df = pd.merge(references_df, top_cited, on="cite_to", how="inner")

    # Get the first title for each cite_to
    first_values = top10_df.groupby("cite_to")[["title", "author", "year"]].first().reset_index()

    # Drop the dirty columns and merge canonical values back
    top10_df = top10_df.drop(columns=["title", "author", "year"]).merge(first_values, on="cite_to", how="left")
    top10_df["year"] = top10_df["year"].astype(str)
    top10_df["year"] = top10_df["year"].str[:-2]
    return (top10_df,)


@app.cell(hide_code=True)
def static_network(alt, df, nx, pd, references_df, top10_df):
    sample_ids_set = set(df["scopus_id"].unique())
    top10_ids_set = set(top10_df["cite_to"].unique())

    ext_refs = references_df[
        references_df["scopus_id"].isin(sample_ids_set) &
        references_df["cite_to"].isin(top10_ids_set)
    ].copy()

    # Build graph
    G1 = nx.DiGraph()

    for node1 in sample_ids_set:
        G1.add_node(node1)

    for _, row1 in top10_df.iterrows():
        G1.add_edge(row1["scopus_id"], row1["cite_to"])

    # Layout
    pos1 = nx.spring_layout(G1, seed=42, k=0.2)



    # Sample nodes
    sample_nodes_data = pd.DataFrame([
        {"scopus_id": node1, "x": pos1[node1][0], "y": pos1[node1][1], "connections": G1.degree(node1)}
        for node1 in G1.nodes() if node1 in sample_ids_set
    ])

    sample_nodes_data = pd.merge(
        sample_nodes_data,
        df[["scopus_id", "Title", "Authors", "Year", "research_approach", "urban/rural"]],
        on="scopus_id", how="left"
    )


    # Top10 outside-sample nodes — ranked by citations_count
    top10_meta = (
        top10_df[top10_df["cite_to"].isin(top10_ids_set)]
        [["cite_to", "title", "author", "year", "citations_count"]]
        .drop_duplicates(subset=["cite_to"])
        .sort_values("citations_count", ascending=False)
        .reset_index(drop=True)
    )

    top10_meta["rank"] = (top10_meta.index + 1).astype(str)

    top10_nodes_data = pd.DataFrame([
        {"scopus_id": node1, "x": pos1[node1][0], "y": pos1[node1][1], "connections": G1.degree(node1)}
        for node1 in G1.nodes() if node1 in top10_ids_set
    ])

    top10_nodes_data = pd.merge(
        top10_nodes_data, top10_meta,
        left_on="scopus_id", right_on="cite_to", how="left"
    )

    # External edge rows
    ext_edge_rows = [
        {"x": pos1[s][0], "y": pos1[s][1], "x2": pos1[t][0], "y2": pos1[t][1], "source": s, "target": t}
        for s, t in G1.edges() if s in sample_ids_set and t in top10_ids_set
    ]
    ext_edge_df = pd.DataFrame(ext_edge_rows)

    # Merge source node's research_approach onto the edge
    ext_edge_df = ext_edge_df.merge(
        sample_nodes_data[["scopus_id", "research_approach"]],
        left_on="source", right_on="scopus_id", how="left"
    ).drop(columns="scopus_id")

    # Hover selection
    hover1 = alt.selection_point(fields=["scopus_id"], on="mouseover", empty=False)


    # External edges
    edge_color_scale = alt.Scale(
        domain=["TD", "LWR"],
        range=["#1F77B4", "#D62728"]
    )

    chart_ext_edges = alt.Chart(ext_edge_df).mark_rule(strokeWidth=0.15).encode(
        x=alt.X("x:Q", axis=None),
        y=alt.Y("y:Q", axis=None),
        x2="x2:Q",
        y2="y2:Q",
        color=alt.Color("research_approach:N", scale=edge_color_scale, legend=None),
        opacity=alt.value(1),
    )


    # Scales
    color_scale = alt.Scale(
        domain=["TD-URBAN", "TD-RURAL", "TD-OTHER", "LRW-URBAN", "LRW-RURAL", "LRW-OTHER"],
        range=["#1F77B4", "#1F77B4", "#1F77B4", "#D62728", "#D62728", "#D62728"]
    )

    shape_scale = alt.Scale(
        domain=["TD-URBAN", "TD-RURAL", "TD-OTHER", "LRW-URBAN", "LRW-RURAL", "LRW-OTHER"],
        range=["circle", "triangle", "square", "circle", "triangle", "square"]
    )


    # Sample nodes
    chart_sample_nodes = alt.Chart(sample_nodes_data).mark_point(
        strokeWidth=1,
        filled=True
    ).encode(
        x=alt.X("x:Q", axis=None),
        y=alt.Y("y:Q", axis=None),
        size=alt.Size("connections:Q", scale=alt.Scale(range=[50, 500]), legend=None),
        color=alt.Color("urban/rural:N", scale=color_scale, legend=alt.Legend(title="Context")),
        shape=alt.Shape("urban/rural:N", scale=shape_scale, legend=alt.Legend(title="Context")),
        opacity=alt.condition(
            alt.datum.connections == 0,
            alt.value(0.25),
            alt.value(0.8)
        ),
        stroke=alt.condition(
            alt.datum.connections == 0,
            alt.value("gray"),
            alt.value("white")
        ),
        tooltip=[
            alt.Tooltip("connections:Q"),
            alt.Tooltip("Title:N"),
            alt.Tooltip("Authors:N"),
            alt.Tooltip("Year:Q"),
            alt.Tooltip("research_approach:N", title="Research Approach"),
            alt.Tooltip("urban/rural:N", title="Context"),
        ]
    ).add_params(hover1)

    # Separate highlight layer for hovered node
    chart_sample_highlight = alt.Chart(sample_nodes_data).mark_point(
        strokeWidth=2,
        filled=True
    ).encode(
        x=alt.X("x:Q", axis=None),
        y=alt.Y("y:Q", axis=None),
        size=alt.Size("connections:Q", scale=alt.Scale(range=[50, 500]), legend=None),
        color=alt.condition(hover1, alt.value("orange"), alt.value("transparent")),
        shape=alt.Shape("urban/rural:N", scale=shape_scale, legend=None),
        opacity=alt.condition(hover1, alt.value(1.0), alt.value(0)),
    )


    # Top10 nodes
    chart_top10_nodes = alt.Chart(top10_nodes_data).mark_circle(stroke="gray", strokeWidth=0.5).encode(
        x=alt.X("x:Q", axis=None),
        y=alt.Y("y:Q", axis=None),
        size=alt.Size("connections:Q", scale=alt.Scale(range=[50, 500]), legend=None),
        color=alt.value("yellow"),
        opacity=alt.value(0.85),
        tooltip=[
            alt.Tooltip("rank:N", title="Rank"),
            alt.Tooltip("title:N", title="Title"),
            alt.Tooltip("author:N", title="Authors"),
            alt.Tooltip("year:N", title="Year"),
            alt.Tooltip("citations_count:N", title="Citations"),
        ]
    )

    # Rank labels
    chart_top10_labels = alt.Chart(top10_nodes_data).mark_text(
        fontSize=10,
        fontWeight="bold",
        color="black",
        dy=1
    ).encode(
        x=alt.X("x:Q", axis=None),
        y=alt.Y("y:Q", axis=None),
        text=alt.Text("rank:N"),
    )


    base = (
        chart_ext_edges + chart_sample_nodes + chart_sample_highlight
    ).properties(
        title="Citation Network — Top 10 Referenced Papers",
        width=600,
        height=500
    )

    top10 = (
        chart_top10_nodes + chart_top10_labels
    )

    network_chart1 = (
        base + top10
    ).resolve_scale(
        color="independent",
        shape="independent"
    ).properties(
        title="Citation Network — Top 10 Referenced Papers",
        width=600,
        height=500)
    #).configure_view(strokeWidth=0)
    return


@app.function
def df_cluster(df, value):
    df2 = df.copy()
    if value!="all":
        df2 = df2.loc[df2["cluster_number"]==value,]
    else:
        df2=df2
    return df2


@app.cell
def _(df, selector):
    df_change=df_cluster(df,selector.value)
    return (df_change,)


@app.cell(hide_code=True)
def interactive_network(alt, df_change, mo, nx, pd, references_df, top10_df):
    # Sets

    v4_sample_ids_set = set(df_change["scopus_id"].unique())
    v4_top10_ids_set = set(top10_df["cite_to"].unique())

    # Internal edges (sample → sample)
    v4_int_refs = references_df[
        references_df["scopus_id"].isin(v4_sample_ids_set) &
        references_df["cite_to"].isin(v4_sample_ids_set)
    ].copy()

    # External edges (sample → top10)
    v4_ext_refs = references_df[
        references_df["scopus_id"].isin(v4_sample_ids_set) &
        references_df["cite_to"].isin(v4_top10_ids_set)
    ].copy()

    # Build graph
    v4_G = nx.DiGraph()

    for node7 in v4_sample_ids_set:
        v4_G.add_node(node7)

    for _, row7 in v4_int_refs.iterrows():
        v4_G.add_edge(row7["scopus_id"], row7["cite_to"])
    for _, row7 in v4_ext_refs.iterrows():
        v4_G.add_edge(row7["scopus_id"], row7["cite_to"])

    # Add top10 nodes explicitly
    for node7 in v4_top10_ids_set:
        v4_G.add_node(node7)

    # Layout
    v4_pos = nx.spring_layout(v4_G, seed=42, k=0.2)

    # Sample nodes
    v4_sample_nodes_data = pd.DataFrame([
        {"scopus_id": node7, "x": v4_pos[node7][0], "y": v4_pos[node7][1], "connections": v4_G.degree(node7)}
        for node7 in v4_G.nodes() if node7 in v4_sample_ids_set
    ])
    v4_sample_nodes_data = pd.merge(
        v4_sample_nodes_data,
        df_change[["scopus_id", "Title", "Authors", "Year", "research_approach", "urban/rural", "cluster_number"]],
        on="scopus_id", how="left"
    )

    # Top10 nodes — ranked by citations_count
    v4_top10_meta = (
        top10_df[top10_df["cite_to"].isin(v4_top10_ids_set)]
        [["cite_to", "title", "author", "year", "citations_count"]]
        .drop_duplicates(subset=["cite_to"])
        .sort_values("citations_count", ascending=False)
        .reset_index(drop=True)
    )
    v4_top10_meta["rank"] = (v4_top10_meta.index + 1).astype(str)

    v4_top10_nodes_data = pd.DataFrame([
        {"scopus_id": node7, "x": v4_pos[node7][0], "y": v4_pos[node7][1], "connections": v4_G.degree(node7)}
        for node7 in v4_G.nodes() if node7 in v4_top10_ids_set
    ])
    v4_top10_nodes_data = pd.merge(
        v4_top10_nodes_data, v4_top10_meta,
        left_on="scopus_id", right_on="cite_to", how="left"
    )

    # Internal edge rows — long format for hover direction coloring
    v4_int_edge_rows = [
        {"x": v4_pos[s][0], "y": v4_pos[s][1], "x2": v4_pos[t][0], "y2": v4_pos[t][1], "source": s, "target": t}
        for s, t in v4_G.edges() if s in v4_sample_ids_set and t in v4_sample_ids_set
    ]
    v4_int_edge_df = pd.DataFrame(v4_int_edge_rows)

    v4_int_edge_long = pd.concat([
        v4_int_edge_df.assign(scopus_id=v4_int_edge_df["source"], role="cited others"),
        v4_int_edge_df.assign(scopus_id=v4_int_edge_df["target"], role="was cited")
    ], ignore_index=True)

    # External edge rows — long format
    v4_ext_edge_rows = [
        {"x": v4_pos[s][0], "y": v4_pos[s][1], "x2": v4_pos[t][0], "y2": v4_pos[t][1], "source": s, "target": t}
        for s, t in v4_G.edges() if s in v4_sample_ids_set and t in v4_top10_ids_set
    ]
    v4_ext_edge_df = pd.DataFrame(v4_ext_edge_rows)

    v4_ext_edge_long = pd.concat([
        v4_ext_edge_df.assign(scopus_id=v4_ext_edge_df["source"], role="cited others"),
        v4_ext_edge_df.assign(scopus_id=v4_ext_edge_df["target"], role="was cited")
    ], ignore_index=True)

    # Hover selection
    v4_hover = alt.selection_point(fields=["scopus_id"], on="click", empty=False)

    # Direction scale — green/purple, distinct from blue, red, yellow
    v4_direction_scale = alt.Scale(
        domain=["cited others", "was cited"],
        range=["#2CA02C", "#9467BD"]
    )

    # Internal edges chart
    v4_chart_int_edges = alt.Chart(v4_int_edge_long).mark_rule(strokeWidth=1).encode(
        x=alt.X("x:Q", axis=None),
        y=alt.Y("y:Q", axis=None),
        x2="x2:Q",
        y2="y2:Q",
        color=alt.condition(
            v4_hover,
            alt.Color("role:N", scale=v4_direction_scale, legend=alt.Legend(title="Direction")),
            alt.value("lightgray")
        ),
        opacity=alt.condition(v4_hover, alt.value(0.9), alt.value(0.12)),
    )

    # External edges chart
    v4_chart_ext_edges = alt.Chart(v4_ext_edge_long).mark_rule(strokeWidth=1.5).encode(
        x=alt.X("x:Q", axis=None),
        y=alt.Y("y:Q", axis=None),
        x2="x2:Q",
        y2="y2:Q",
        color=alt.condition(
            v4_hover,
            alt.Color("role:N", scale=v4_direction_scale, legend=None),
            alt.value("lightgray")
        ),
        opacity=alt.condition(v4_hover, alt.value(0.9), alt.value(0.12)),
    )

    # Node scales
    v4_color_scale = alt.Scale(
        domain=["TD-URBAN", "TD-RURAL", "TD-OTHER", "LRW-URBAN", "LRW-RURAL", "LRW-OTHER"],
        range=["#1F77B4", "#1F77B4", "#1F77B4", "#D62728", "#D62728", "#D62728"]
    )
    v4_shape_scale = alt.Scale(
        domain=["TD-URBAN", "TD-RURAL", "TD-OTHER", "LRW-URBAN", "LRW-RURAL", "LRW-OTHER"],
        range=["circle", "triangle", "square", "circle", "triangle", "square"]
    )

    # Sample nodes
    v4_chart_sample_nodes = alt.Chart(v4_sample_nodes_data).mark_point(
        strokeWidth=1,
        filled=True
    ).encode(
        x=alt.X("x:Q", axis=None),
        y=alt.Y("y:Q", axis=None),
        size=alt.Size("connections:Q", scale=alt.Scale(range=[50, 500]), legend=None),
        color=alt.Color("urban/rural:N", scale=v4_color_scale, legend=alt.Legend(title="Context")),
        shape=alt.Shape("urban/rural:N", scale=v4_shape_scale, legend=alt.Legend(title="Context")),
        opacity=alt.condition(
            alt.datum.connections == 0,
            alt.value(0.25),
            alt.value(0.8)
        ),
        stroke=alt.condition(
            alt.datum.connections == 0,
            alt.value("gray"),
            alt.value("white")
        ),
        tooltip=[
            alt.Tooltip("connections:Q"),
            alt.Tooltip("Title:N"),
            alt.Tooltip("Authors:N"),
            alt.Tooltip("Year:Q"),
            alt.Tooltip("research_approach:N", title="Research Approach"),
            alt.Tooltip("urban/rural:N", title="Context"),
            alt.Tooltip("cluster_number:N", title="Cluster")
        ]
    ).add_params(v4_hover)

    # Highlight layer
    v4_chart_sample_highlight = alt.Chart(v4_sample_nodes_data).mark_point(
        strokeWidth=2,
        filled=True
    ).encode(
        x=alt.X("x:Q", axis=None),
        y=alt.Y("y:Q", axis=None),
        size=alt.Size("connections:Q", scale=alt.Scale(range=[50, 500]), legend=None),
        color=alt.condition(v4_hover, alt.value("orange"), alt.value("transparent")),
        shape=alt.Shape("urban/rural:N", scale=v4_shape_scale, legend=None),
        opacity=alt.condition(v4_hover, alt.value(1.0), alt.value(0)),
    )

    # Top10 nodes
    v4_chart_top10_nodes = alt.Chart(v4_top10_nodes_data).mark_circle(stroke="gray", strokeWidth=0.5).encode(
        x=alt.X("x:Q", axis=None),
        y=alt.Y("y:Q", axis=None),
        size=alt.Size("connections:Q", scale=alt.Scale(range=[50, 500]), legend=None),
        color=alt.value("yellow"),
        opacity=alt.value(0.85),
        tooltip=[
            alt.Tooltip("rank:N", title="Rank"),
            alt.Tooltip("title:N", title="Title"),
            alt.Tooltip("author:N", title="Authors"),
            alt.Tooltip("year:N", title="Year"),
            alt.Tooltip("citations_count:N", title="Citations"),
        ]
    )

    # Rank labels
    v4_chart_top10_labels = alt.Chart(v4_top10_nodes_data).mark_text(
        fontSize=10,
        fontWeight="bold",
        color="black",
        dy=1
    ).encode(
        x=alt.X("x:Q", axis=None),
        y=alt.Y("y:Q", axis=None),
        text=alt.Text("rank:N"),
    )

    network_chart_v4 = (
        v4_chart_int_edges + v4_chart_ext_edges + v4_chart_sample_nodes + v4_chart_sample_highlight + v4_chart_top10_nodes + v4_chart_top10_labels
    ).resolve_scale(
        color="independent",
        shape="independent"
    ).properties(
        title="Citation Network — Top 10 Referenced Papers",
        width=500,
        height=500
    ).interactive()

    v4_interactive_chart = mo.ui.altair_chart(network_chart_v4)
    return (
        v4_interactive_chart,
        v4_sample_ids_set,
        v4_sample_nodes_data,
        v4_top10_ids_set,
        v4_top10_nodes_data,
    )


@app.cell(hide_code=True)
def interactive_table(
    df_change,
    mo,
    references_df,
    top10_df,
    v4_interactive_chart,
    v4_sample_ids_set,
    v4_sample_nodes_data,
    v4_top10_ids_set,
    v4_top10_nodes_data,
):
    v4_selected_sample = v4_interactive_chart.apply_selection(v4_sample_nodes_data)
    v4_selected_top10 = v4_interactive_chart.apply_selection(v4_top10_nodes_data)

    try:
        # Check which node type was clicked
        if len(v4_selected_sample) > 0:
            v4_selected_id = v4_selected_sample["scopus_id"].iloc[0]

            v4_node_refs_in_sample = references_df[
                (references_df["scopus_id"] == v4_selected_id) &
                (references_df["cite_to"].isin(v4_sample_ids_set))
            ][["cite_to"]].drop_duplicates().merge(
                df_change[["scopus_id", "Title", "Authors", "Year"]],
                left_on="cite_to", right_on="scopus_id", how="left"
            ).drop(columns="scopus_id")

            v4_cited_top10_ids = references_df[
                (references_df["scopus_id"] == v4_selected_id) &
                (references_df["cite_to"].isin(v4_top10_ids_set))
            ]["cite_to"]

            v4_node_refs_top10 = top10_df[
                top10_df["cite_to"].isin(v4_cited_top10_ids)
            ].drop_duplicates(subset=["cite_to"])[["cite_to", "title", "author", "year", "citations_count"]]

            v4_cited_by = references_df[
                (references_df["cite_to"] == v4_selected_id) &
                (references_df["scopus_id"].isin(v4_sample_ids_set))
            ][["scopus_id"]].drop_duplicates().merge(
                df_change[["scopus_id", "Title", "Authors", "Year"]],
                on="scopus_id", how="left"
            )

            result = mo.vstack([
                mo.md(f"### {v4_selected_sample['Title'].iloc[0]} ({v4_selected_sample['Year'].iloc[0]})"),
                mo.md(f"**Cites these top 10 papers ({len(v4_node_refs_top10)}):**"),
                v4_node_refs_top10,
                mo.md(f"**Cites these sample papers ({len(v4_node_refs_in_sample)}):**"),
                v4_node_refs_in_sample,
                mo.md(f"**Cited by these sample papers ({len(v4_cited_by)}):**"),
                v4_cited_by,
            ], gap=0)

        elif len(v4_selected_top10) > 0:
            v4_selected_id = v4_selected_top10["scopus_id"].iloc[0]

            v4_top10_info = v4_top10_nodes_data[
                v4_top10_nodes_data["scopus_id"] == v4_selected_id
            ]

            v4_cited_by_sample = references_df[
                (references_df["cite_to"] == v4_selected_id) &
                (references_df["scopus_id"].isin(v4_sample_ids_set))
            ][["scopus_id"]].drop_duplicates().merge(
                df_change[["scopus_id", "Title", "Authors", "Year", "research_approach", "urban/rural"]],
                on="scopus_id", how="left"
            )

            result = mo.vstack([
                mo.md(f"### {v4_top10_info['title'].iloc[0]} ({v4_top10_info['year'].iloc[0]})"),
                mo.md(f"**Authors:** {v4_top10_info['author'].iloc[0]}"),
                mo.md(f"**Citations:** {v4_top10_info['citations_count'].iloc[0]} | **Rank:** {v4_top10_info['rank'].iloc[0]}"),
                mo.md(f"**Cited by these sample papers ({len(v4_cited_by_sample)}):**"),
                v4_cited_by_sample,
            ])

        else:
            result = mo.md("_Click a node to see its connections._")

    except:
        result = mo.md("_Click a node to see its connections._")
    return (result,)


@app.cell
def _(selector):
    selector
    return


@app.cell(hide_code=True)
def _(mo, result, v4_interactive_chart):
    mo.hstack([
        v4_interactive_chart,
        mo.Html(f'<div style="height:600px; overflow-y:auto; overflow-x:auto; padding-right:8px;">{mo.as_html(result).text}</div>')
    ])
    return


if __name__ == "__main__":
    app.run()
