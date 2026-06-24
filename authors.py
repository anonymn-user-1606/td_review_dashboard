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
app = marimo.App(width="medium")


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

    return mo, pd


@app.cell
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

    #Getting the eids into a list
    eids2 = df2["EID"].tolist()
    df=df2


    sheet_name2 = "references_df"

    url2 = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={sheet_name2}"

    references_df = pd.read_csv(url2)
    references_df["scopus_id"] = references_df["scopus_id"].astype(str)
    return df, references_df


@app.cell
def pickle_loading():
    #saving it into a pickle
    #with open('pickles/articles_raw_list.pkl', 'wb') as file:
    #    articles_ = pickle.dump(articles, file)

    #with open('pickles/articles_raw_list.pkl', 'rb') as file:
    #    articles = pickle.load(file)
    return


@app.cell
def reference_df_creation():
    """

    ids = []
    refs = []
    titles = []
    autores = []
    años = []

    for j in range(len(articles)):
        if articles[j].references is not None:
            for art in articles[j].references:
                ids.append(str(articles[j].identifier))
                refs.append(art.id)
                titles.append(art.title)
                autores.append(art.authors)
                años.append(art.publicationyear)
        else:
            ids.append(str(articles[j].identifier))
            refs.append("no references in metadata")
            titles.append("no references in metadata")
            autores.append("no references in metadata")
            años.append("no references in metadata")

    references_dict = {
        "scopus_id": ids,
        "cite_to": refs,
        "title": titles,
        "author": autores,
        "year": años
    }

    references_df = pd.DataFrame(references_dict)"""
    return


@app.cell
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
    return (top10_df,)


@app.cell
def _(top10_df):
    top10_df
    return


@app.cell
def _(alt, df, nx, pd, references_df, top10_df):
    # Sets
    _sample_ids_set = set(df["scopus_id"].unique())
    _top10_ids_set = set(top10_df["cite_to"].unique())
    _top10_outside = _top10_ids_set

    # Internal edges (sample → sample)
    _int_refs = references_df[
        references_df["scopus_id"].isin(_sample_ids_set) &
        references_df["cite_to"].isin(_sample_ids_set)
    ].copy()

    # External edges (sample → top10)
    _ext_refs = references_df[
        references_df["scopus_id"].isin(_sample_ids_set) &
        references_df["cite_to"].isin(_top10_outside)
    ].copy()

    # Build graph
    _G2 = nx.DiGraph()

    for node in _sample_ids_set:
        _G2.add_node(node)

    for _, row in _int_refs.iterrows():
        _G2.add_edge(row["scopus_id"], row["cite_to"])
    for _, row in _ext_refs.iterrows():
        _G2.add_edge(row["scopus_id"], row["cite_to"])

    # Layout
    _pos2 = nx.spring_layout(_G2, seed=42, k=0.2)
    #_pos2 = nx.spectral_layout(_G2)

    # Sample nodes
    _sample_nodes_data = pd.DataFrame([
        {"scopus_id": n, "x": _pos2[n][0], "y": _pos2[n][1], "connections": _G2.degree(n)}
        for n in _G2.nodes() if n in _sample_ids_set
    ])
    _sample_nodes_data = pd.merge(
        _sample_nodes_data,
        df[["scopus_id", "Title", "Authors", "Year", "research_approach"]],
        on="scopus_id", how="left"
    )

    # Top10 outside-sample nodes
    _top10_meta = top10_df[top10_df["cite_to"].isin(_top10_outside)][["cite_to", "title", "author", "year","citations_count"]].drop_duplicates(subset=["cite_to"])
    _top10_nodes_data = pd.DataFrame([
        {"scopus_id": n, "x": _pos2[n][0], "y": _pos2[n][1], "connections": _G2.degree(n)}
        for n in _G2.nodes() if n in _top10_outside
    ])
    _top10_nodes_data = pd.merge(_top10_nodes_data, _top10_meta, left_on="scopus_id", right_on="cite_to", how="left")

    # Internal edge rows
    _int_edge_rows = [
        {"x": _pos2[s][0], "y": _pos2[s][1], "x2": _pos2[t][0], "y2": _pos2[t][1], "source": s, "target": t}
        for s, t in _G2.edges() if s in _sample_ids_set and t in _sample_ids_set
    ]
    _int_edge_df = pd.DataFrame(_int_edge_rows)

    # External edge rows
    _ext_edge_rows = [
        {"x": _pos2[s][0], "y": _pos2[s][1], "x2": _pos2[t][0], "y2": _pos2[t][1], "source": s, "target": t}
        for s, t in _G2.edges() if s in _sample_ids_set and t in _top10_outside
    ]

    _ext_edge_df = pd.DataFrame(_ext_edge_rows)

    _ext_edge_long = pd.concat([
        _ext_edge_df.assign(scopus_id=_ext_edge_df["source"], role="cited others"),
        _ext_edge_df.assign(scopus_id=_ext_edge_df["target"], role="was cited")
    ], ignore_index=True)


    # Hover selection on sample nodes
    _hover3 = alt.selection_point(fields=["scopus_id"], on="mouseover", empty=False)

    # Internal edges — long format for hover direction coloring
    _int_edge_long = pd.concat([
        _int_edge_df.assign(scopus_id=_int_edge_df["source"], role="cited others"),
        _int_edge_df.assign(scopus_id=_int_edge_df["target"], role="was cited")
    ], ignore_index=True)

    _direction_scale = alt.Scale(domain=["cited others", "was cited"], range=["red", "green"])

    # Internal edges chart (hover-based coloring)
    _chart_int_edges = alt.Chart(_int_edge_long).mark_rule(strokeWidth=1).encode(
        x=alt.X("x:Q", axis=None),
        y=alt.Y("y:Q", axis=None),
        x2="x2:Q",
        y2="y2:Q",
        color=alt.condition(
            _hover3,
            alt.Color("role:N", scale=_direction_scale, legend=alt.Legend(title="Direction")),
            alt.value("lightgray")
        ),
        opacity=alt.condition(_hover3, alt.value(0.9), alt.value(0.15)),
    )

    # External edges chart (static red — sample cited top10)
    _chart_ext_edges = alt.Chart(_ext_edge_long).mark_rule(strokeWidth=1.5).encode(
        x=alt.X("x:Q", axis=None),
        y=alt.Y("y:Q", axis=None),
        x2="x2:Q",
        y2="y2:Q",
        color=alt.condition(_hover3, alt.value("red"), alt.value("lightgray")),
        opacity=alt.condition(_hover3, alt.value(0.9), alt.value(0.15)),
    )

    # Sample nodes (circles, colored by research_approach)
    _research_approach_scale = alt.Scale(
        domain=["TD", "LWR"],
        range=["#8338EC", "#F72585"]
    )

    _chart_sample_nodes = alt.Chart(_sample_nodes_data).mark_circle(stroke="white", strokeWidth=1).encode(
        x=alt.X("x:Q", axis=None),
        y=alt.Y("y:Q", axis=None),
        size=alt.Size("connections:Q", scale=alt.Scale(range=[50, 500]), legend=None),
        color=alt.condition(
            _hover3,
            alt.value("orange"),
            alt.Color("research_approach:N", scale=_research_approach_scale, legend=alt.Legend(title="Research Approach"))
        ),
        opacity=alt.condition(
            alt.datum.connections == 0,
            alt.value(0.25),  # isolated nodes are faded
            alt.value(0.8)    # connected nodes are normal
        ),
        stroke=alt.condition(
            alt.datum.connections == 0,
            alt.value("gray"),   # subtle gray border for isolated
            alt.value("white")   # white border for connected
        ),
        tooltip=[
            alt.Tooltip("connections:Q"),
            alt.Tooltip("Title:N"),
            alt.Tooltip("Authors:N"),
            alt.Tooltip("Year:Q"),
            alt.Tooltip("research_approach:N", title="Research Approach")
        ]
    ).add_params(_hover3)

    # Top10 outside-sample nodes (squares, yellow)
    _chart_top10_nodes = alt.Chart(_top10_nodes_data).mark_circle(stroke="gray", strokeWidth=0.5).encode(
        x=alt.X("x:Q", axis=None),
        y=alt.Y("y:Q", axis=None),
        size=alt.Size("connections:Q", scale=alt.Scale(range=[50, 500]), legend=None),
        color=alt.value("yellow"),
        opacity=alt.value(0.85),
        tooltip=[
            alt.Tooltip("title:N", title="Title"),
            alt.Tooltip("author:N", title="Authors"),
            alt.Tooltip("year:N", title="Year"),
            alt.Tooltip("citations_count:N", title="Citations"),
        ]
    )

    network_chart4 = (
        _chart_int_edges + _chart_ext_edges + _chart_sample_nodes + _chart_top10_nodes
    ).resolve_scale(
        color="independent"
        ).properties(
        title="Citation Network incl. Top 10 Referenced Papers",
        width=500,
        height=500
    ).configure_view(strokeWidth=0)

    network_chart4
    return


@app.cell
def _(alt, df, nx, pd, references_df, top10_df):
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

    network_chart1
    return


@app.cell
def _(alt, df, mo, nx, pd, references_df, top10_df):
    # Sets
    v4_sample_ids_set = set(df["scopus_id"].unique())
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
        df[["scopus_id", "Title", "Authors", "Year", "research_approach", "urban/rural"]],
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
        width=700,
        height=500
    ).interactive()

    v4_interactive_chart = mo.ui.altair_chart(network_chart_v4)
    v4_interactive_chart
    return (
        v4_interactive_chart,
        v4_sample_ids_set,
        v4_sample_nodes_data,
        v4_top10_ids_set,
    )


@app.cell
def _(
    df,
    mo,
    references_df,
    top10_df,
    v4_interactive_chart,
    v4_sample_ids_set,
    v4_sample_nodes_data,
    v4_top10_ids_set,
):
    v4_selected = v4_interactive_chart.apply_selection(v4_sample_nodes_data)

    try:
        v4_selected_id = v4_selected["scopus_id"].iloc[0]

        v4_node_refs_in_sample = references_df[
            (references_df["scopus_id"] == v4_selected_id) &
            (references_df["cite_to"].isin(v4_sample_ids_set))
        ][["cite_to"]].drop_duplicates().merge(
            df[["scopus_id", "Title", "Authors", "Year"]],
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
            df[["scopus_id", "Title", "Authors", "Year"]],
            on="scopus_id", how="left"
        )

        result = mo.vstack([
            mo.md(f"### {v4_selected['Title'].iloc[0]} ({v4_selected['Year'].iloc[0]})"),
            mo.md(f"**Cites these sample papers ({len(v4_node_refs_in_sample)}):**"),
            v4_node_refs_in_sample,
            mo.md(f"**Cites these top 10 papers ({len(v4_node_refs_top10)}):**"),
            v4_node_refs_top10,
            mo.md(f"**Cited by these sample papers ({len(v4_cited_by)}):**"),
            v4_cited_by,
        ])
    except:
        result = mo.md("_Click a node to see its connections._")

    result
    return


@app.cell
def _(alt, df, nx, pd, references_df, top10_df):
    # Sets
    _v3_sample_ids_set = set(df["scopus_id"].unique())
    _v3_top10_ids_set = set(top10_df["cite_to"].unique())
    #_v3_top10_outside = _v3_top10_ids_set - _v3_sample_ids_set
    _v3_top10_outside = _v3_top10_ids_set

    # External edges only (sample → top10)
    _v3_ext_refs = references_df[
        references_df["scopus_id"].isin(_v3_sample_ids_set) &
        references_df["cite_to"].isin(_v3_top10_outside)
    ].copy()

    # Build graph
    _v3_G = nx.DiGraph()
    for node6 in _v3_sample_ids_set:
        _v3_G.add_node(node6)
    for _, row6 in _v3_ext_refs.iterrows():
        _v3_G.add_edge(row6["scopus_id"], row6["cite_to"])

    # Layout
    _v3_pos = nx.spring_layout(_v3_G, seed=42, k=0.2)

    # Sample nodes
    _v3_sample_nodes_data = pd.DataFrame([
        {"scopus_id": node6, "x": _v3_pos[node6][0], "y": _v3_pos[node6][1], "connections": _v3_G.degree(node6)}
        for node6 in _v3_G.nodes() if node6 in _v3_sample_ids_set
    ])
    _v3_sample_nodes_data = pd.merge(
        _v3_sample_nodes_data,
        df[["scopus_id", "Title", "Authors", "Year", "research_approach", "urban/rural"]],
        on="scopus_id", how="left"
    )

    # Top10 outside-sample nodes — ranked by citations_count
    _v3_top10_meta = (
        top10_df[top10_df["cite_to"].isin(_v3_top10_outside)]
        [["cite_to", "title", "author", "year", "citations_count"]]
        .drop_duplicates(subset=["cite_to"])
        .sort_values("citations_count", ascending=False)
        .reset_index(drop=True)
    )
    _v3_top10_meta["rank"] = (_v3_top10_meta.index + 1).astype(str)

    _v3_top10_nodes_data = pd.DataFrame([
        {"scopus_id": node6, "x": _v3_pos[node6][0], "y": _v3_pos[node6][1], "connections": _v3_G.degree(node6)}
        for node6 in _v3_G.nodes() if node6 in _v3_top10_outside
    ])
    _v3_top10_nodes_data = pd.merge(
        _v3_top10_nodes_data, _v3_top10_meta,
        left_on="scopus_id", right_on="cite_to", how="left"
    )

    # External edge rows
    _v3_ext_edge_rows = [
        {"x": _v3_pos[s][0], "y": _v3_pos[s][1], "x2": _v3_pos[t][0], "y2": _v3_pos[t][1], "source": s, "target": t}
        for s, t in _v3_G.edges() if s in _v3_sample_ids_set and t in _v3_top10_outside
    ]
    _v3_ext_edge_df = pd.DataFrame(_v3_ext_edge_rows)

    # Merge source node's research_approach onto the edge
    _v3_ext_edge_df = _v3_ext_edge_df.merge(
        _v3_sample_nodes_data[["scopus_id", "research_approach"]],
        left_on="source", right_on="scopus_id", how="left"
    ).drop(columns="scopus_id")

    # Hover selection
    _v3_hover = alt.selection_point(fields=["scopus_id"], on="mouseover", empty=False)

    # External edges
    _v3_edge_color_scale = alt.Scale(
        domain=["TD", "LWR"],
        range=["#1F77B4", "#D62728"]
    )

    _v3_chart_ext_edges = alt.Chart(_v3_ext_edge_df).mark_rule(strokeWidth=0.15).encode(
        x=alt.X("x:Q", axis=None),
        y=alt.Y("y:Q", axis=None),
        x2="x2:Q",
        y2="y2:Q",
        color=alt.Color("research_approach:N", scale=_v3_edge_color_scale, legend=None),
        opacity=alt.value(1),
    )

    # Scales
    _v3_color_scale = alt.Scale(
        domain=["TD-URBAN", "TD-RURAL", "TD-OTHER", "LRW-URBAN", "LRW-RURAL", "LRW-OTHER"],
        range=["#1F77B4", "#1F77B4", "#1F77B4", "#D62728", "#D62728", "#D62728"]
    )

    _v3_shape_scale = alt.Scale(
        domain=["TD-URBAN", "TD-RURAL", "TD-OTHER", "LRW-URBAN", "LRW-RURAL", "LRW-OTHER"],
        range=["circle", "triangle", "square", "circle", "triangle", "square"]
    )

    # Sample nodes
    _v3_chart_sample_nodes = alt.Chart(_v3_sample_nodes_data).mark_point(
        strokeWidth=1,
        filled=True
    ).encode(
        x=alt.X("x:Q", axis=None),
        y=alt.Y("y:Q", axis=None),
        size=alt.Size("connections:Q", scale=alt.Scale(range=[50, 500]), legend=None),
        color=alt.Color("urban/rural:N", scale=_v3_color_scale, legend=alt.Legend(title="Context")),
        shape=alt.Shape("urban/rural:N", scale=_v3_shape_scale, legend=alt.Legend(title="Context")),
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
    ).add_params(_v3_hover)

    # Separate highlight layer for hovered node
    _v3_chart_sample_highlight = alt.Chart(_v3_sample_nodes_data).mark_point(
        strokeWidth=2,
        filled=True
    ).encode(
        x=alt.X("x:Q", axis=None),
        y=alt.Y("y:Q", axis=None),
        size=alt.Size("connections:Q", scale=alt.Scale(range=[50, 500]), legend=None),
        color=alt.condition(_v3_hover, alt.value("orange"), alt.value("transparent")),
        shape=alt.Shape("urban/rural:N", scale=_v3_shape_scale, legend=None),
        opacity=alt.condition(_v3_hover, alt.value(1.0), alt.value(0)),
    )

    # Top10 nodes
    _v3_chart_top10_nodes = alt.Chart(_v3_top10_nodes_data).mark_circle(stroke="gray", strokeWidth=0.5).encode(
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
    _v3_chart_top10_labels = alt.Chart(_v3_top10_nodes_data).mark_text(
        fontSize=10,
        fontWeight="bold",
        color="black",
        dy=1
    ).encode(
        x=alt.X("x:Q", axis=None),
        y=alt.Y("y:Q", axis=None),
        text=alt.Text("rank:N"),
    )

    _v3_base = (
        _v3_chart_ext_edges + _v3_chart_sample_nodes + _v3_chart_sample_highlight
    ).properties(
        title="Citation Network — Top 10 Referenced Papers",
        width=600,
        height=500
    )

    _v3_top10 = (
        _v3_chart_top10_nodes + _v3_chart_top10_labels
    )

    network_chart56 = (
        _v3_base + _v3_top10
    ).resolve_scale(
        color="independent",
        shape="independent"
    ).properties(
        title="Citation Network — Top 10 Referenced Papers",
        width=600,
        height=500)
    #).configure_view(strokeWidth=0)

    network_chart56
    return (network_chart56,)


@app.cell
def _():
    """

    top10_summary = (
        top10_df[["cite_to", "title", "author", "year", "citations_count"]]
        .drop_duplicates(subset=["cite_to"])
        .sort_values("citations_count", ascending=False)
        .reset_index(drop=True)
        .assign(rank=lambda x: x.index + 1)
        [["rank", "title", "author", "year", "citations_count"]]
        .rename(columns={
            "rank": "Node_number",
            "title": "Title",
            "author": "Authors",
            "year": "Year",
            "citations_count": "Citations"
        })
    )

    top10_summary"""
    return


@app.cell
def _(top10_summary):
    top10_summary
    return


@app.cell
def _(alt, network_chart56, pd, top10_df):
    def truncate_title(title, max_words=7):
        words = str(title).split()
        if len(words) <= max_words:
            return title
        return " ".join(words[:max_words]) + "…"

    def truncate_authors(authors):
        parts = str(authors).split(";")
        if len(parts) <= 1:
            return authors.strip()
        return parts[0].strip() + " et al."

    top10_summary = (
        top10_df[["cite_to", "title", "author", "year", "citations_count"]]
        .drop_duplicates(subset=["cite_to"])
        .sort_values("citations_count", ascending=False)
        .reset_index(drop=True)
        .assign(rank=lambda x: x.index + 1)
        [["rank", "title", "author", "year", "citations_count"]]
        .rename(columns={
            "rank":            "rank",
            "title":           "Title",
            "author":          "Authors",
            "year":            "Year",
            "citations_count": "Citations",
        })
        .assign(
            Title=lambda x: x["Title"].map(truncate_title),
            Authors=lambda x: x["Authors"].map(truncate_authors),
        )
    )

    # ── build the long-form data correctly ──────────────────────────────────────
    col_order = ["rank", "Title", "Authors", "Year", "Citations"]

    top10_plot = top10_summary.copy()
    top10_plot["row"] = top10_plot["rank"]   # separate key for Y positioning

    top10_long = top10_plot.melt(
        id_vars=["row"],
        value_vars=["rank", "Title", "Authors", "Year", "Citations"],
        var_name="column",
        value_name="value"
    )
    top10_long["value"] = top10_long["value"].astype(str)

    # pad for proportional column widths
    pad = {"rank": 3, "Title": 42, "Authors": 25, "Year": 5, "Citations": 8}
    top10_long["value"] = top10_long.apply(
        lambda r: str(r["value"]).ljust(pad[r["column"]]), axis=1
    )

    # ── header ───────────────────────────────────────────────────────────────────
    header_df = pd.DataFrame({
        "column": col_order,
        "value":  col_order,
        "row":    [0] * len(col_order),
    })

    # ── layers ───────────────────────────────────────────────────────────────────
    row_bg = alt.Chart(top10_long).mark_rect(
        stroke="#cccccc", strokeWidth=0.5
    ).encode(
        x=alt.X("column:O", sort=col_order, axis=None),
        y=alt.Y("row:O", sort="ascending", axis=None),
        color=alt.condition(
            "datum.row % 2 == 0",
            alt.value("#f0f0f0"),
            alt.value("#ffffff")
        )
    )

    row_text = alt.Chart(top10_long).mark_text(
        align="left", baseline="middle", fontSize=9, dx=4, color="#111111"
    ).encode(
        x=alt.X("column:O", sort=col_order, axis=None),
        y=alt.Y("row:O", sort="ascending", axis=None),
        text=alt.Text("value:N"),
    )

    hdr_bg = alt.Chart(header_df).mark_rect(
        color="#2c2c2c", stroke="#2c2c2c", strokeWidth=0.5
    ).encode(
        x=alt.X("column:O", sort=col_order, axis=None),
        y=alt.Y("row:O", axis=None),
    )

    hdr_text = alt.Chart(header_df).mark_text(
        align="left", baseline="middle", fontSize=9,
        fontWeight="bold", dx=4, color="white"
    ).encode(
        x=alt.X("column:O", sort=col_order, axis=None),
        y=alt.Y("row:O", axis=None),
        text=alt.Text("value:N"),
    )

    table_chart = (row_bg + row_text + hdr_bg + hdr_text).properties(
        width=550,
        height=alt.Step(22)
    )


    alt.hconcat(network_chart56, table_chart).resolve_scale(
        color="independent"
    ).configure_view(strokeWidth=0)
    return table_chart, top10_summary


@app.cell
def _(table_chart):
    table_chart
    return


@app.cell
def _(top10_df):
    top10_df.groupby(by="title").count()
    return


@app.cell
def _(alt, df, nx, pd, references_df, top10_df):
    # Sets
    _sample_ids_set = set(df["scopus_id"].unique())
    _top10_ids_set = set(top10_df["cite_to"].unique())
    _top10_outside = _top10_ids_set - _sample_ids_set

    # Internal edges (sample → sample)
    _int_refs = references_df[
        references_df["scopus_id"].isin(_sample_ids_set) &
        references_df["cite_to"].isin(_sample_ids_set)
    ].copy()

    # External edges (sample → top10)
    _ext_refs = references_df[
        references_df["scopus_id"].isin(_sample_ids_set) &
        references_df["cite_to"].isin(_top10_outside)
    ].copy()

    # Build graph
    _G2 = nx.DiGraph()

    for _node in _sample_ids_set:
        _G2.add_node(_node)

    for _, _row in _int_refs.iterrows():
        _G2.add_edge(_row["scopus_id"], _row["cite_to"])
    for _, _row in _ext_refs.iterrows():
        _G2.add_edge(_row["scopus_id"], _row["cite_to"])

    # Layout
    _pos2 = nx.spring_layout(_G2, seed=42, k=0.2)
    #_pos2 = nx.spectral_layout(_G2)

    # Sample nodes
    _sample_nodes_data = pd.DataFrame([
        {"scopus_id": n, "x": _pos2[n][0], "y": _pos2[n][1], "connections": _G2.degree(n)}
        for n in _G2.nodes() if n in _sample_ids_set
    ])

    _sample_nodes_data = pd.merge(
        _sample_nodes_data,
        df[["scopus_id", "Title", "Authors", "Year", "research_approach", "cluster_number"]],
        on="scopus_id", how="left"
    )
    _sample_nodes_data["cluster_number"] = _sample_nodes_data["cluster_number"].fillna("No cluster").astype(str)


    # Top10 outside-sample nodes
    _top10_meta = top10_df[top10_df["cite_to"].isin(_top10_outside)][["cite_to", "title", "author", "year","citations_count"]].drop_duplicates(subset=["cite_to"])
    _top10_nodes_data = pd.DataFrame([
        {"scopus_id": n, "x": _pos2[n][0], "y": _pos2[n][1], "connections": _G2.degree(n)}
        for n in _G2.nodes() if n in _top10_outside
    ])
    _top10_nodes_data = pd.merge(_top10_nodes_data, _top10_meta, left_on="scopus_id", right_on="cite_to", how="left")

    # Internal edge rows
    _int_edge_rows = [
        {"x": _pos2[s][0], "y": _pos2[s][1], "x2": _pos2[t][0], "y2": _pos2[t][1], "source": s, "target": t}
        for s, t in _G2.edges() if s in _sample_ids_set and t in _sample_ids_set
    ]
    _int_edge_df = pd.DataFrame(_int_edge_rows)

    # External edge rows
    _ext_edge_rows = [
        {"x": _pos2[s][0], "y": _pos2[s][1], "x2": _pos2[t][0], "y2": _pos2[t][1], "source": s, "target": t}
        for s, t in _G2.edges() if s in _sample_ids_set and t in _top10_outside
    ]

    _ext_edge_df = pd.DataFrame(_ext_edge_rows)

    _ext_edge_long = pd.concat([
        _ext_edge_df.assign(scopus_id=_ext_edge_df["source"], role="cited others"),
        _ext_edge_df.assign(scopus_id=_ext_edge_df["target"], role="was cited")
    ], ignore_index=True)


    # Hover selection on sample nodes
    _hover3 = alt.selection_point(fields=["scopus_id"], on="mouseover", empty=False)

    # Internal edges — long format for hover direction coloring
    _int_edge_long = pd.concat([
        _int_edge_df.assign(scopus_id=_int_edge_df["source"], role="cited others"),
        _int_edge_df.assign(scopus_id=_int_edge_df["target"], role="was cited")
    ], ignore_index=True)

    _direction_scale = alt.Scale(domain=["cited others", "was cited"], range=["red", "green"])

    # Internal edges chart (hover-based coloring)
    _chart_int_edges = alt.Chart(_int_edge_long).mark_rule(strokeWidth=1).encode(
        x=alt.X("x:Q", axis=None),
        y=alt.Y("y:Q", axis=None),
        x2="x2:Q",
        y2="y2:Q",
        color=alt.condition(
            _hover3,
            alt.Color("role:N", scale=_direction_scale, legend=alt.Legend(title="Direction")),
            alt.value("lightgray")
        ),
        opacity=alt.condition(_hover3, alt.value(0.9), alt.value(0.15)),
    )

    # External edges chart (static red — sample cited top10)
    _chart_ext_edges = alt.Chart(_ext_edge_long).mark_rule(strokeWidth=1.5).encode(
        x=alt.X("x:Q", axis=None),
        y=alt.Y("y:Q", axis=None),
        x2="x2:Q",
        y2="y2:Q",
        color=alt.condition(_hover3, alt.value("red"), alt.value("lightgray")),
        opacity=alt.condition(_hover3, alt.value(0.9), alt.value(0.15)),
    )

    # Sample nodes (circles, colored by research_approach)
    _research_approach_scale = alt.Scale(
        domain=["TD", "LL or RWL"],
        range=["#8338EC", "#F72585"]
    )

    _cluster_scale = alt.Scale(
        domain=["1", "2", "3", "4", "5", "6", "7", "8", "9", "No cluster"],
        range=["#1b9e77", "#d95f02", "#7570b3", "#c9184a", "#66a61e", "#e6ab02", "#a6761d", "#00b4d8", "#1f78b4", "#000000"]
    )

    _chart_sample_nodes = alt.Chart(_sample_nodes_data).mark_square(stroke="white", strokeWidth=1).encode(
        x=alt.X("x:Q", axis=None),
        y=alt.Y("y:Q", axis=None),
        size=alt.Size("connections:Q", scale=alt.Scale(range=[50, 500]), legend=None),
        color=alt.condition(
            _hover3,
            alt.value("orange"),
            alt.Color("cluster_number:N", scale=_cluster_scale, legend=alt.Legend(title="Cluster"))
        ),
        opacity=alt.condition(
            alt.datum.connections == 0,
            alt.value(0.25),  # isolated nodes are faded
            alt.value(0.8)    # connected nodes are normal
        ),
        stroke=alt.condition(
            alt.datum.connections == 0,
            alt.value("gray"),   # subtle gray border for isolated
            alt.value("white")   # white border for connected
        ),
        tooltip=[
            alt.Tooltip("connections:Q"),
            alt.Tooltip("Title:N"),
            alt.Tooltip("Authors:N"),
            alt.Tooltip("Year:Q"),
            alt.Tooltip("research_approach:N", title="Research Approach")
        ]
    ).add_params(_hover3)

    # Top10 outside-sample nodes (squares, yellow)
    _chart_top10_nodes = alt.Chart(_top10_nodes_data).mark_circle(stroke="gray", strokeWidth=0.5).encode(
        x=alt.X("x:Q", axis=None),
        y=alt.Y("y:Q", axis=None),
        size=alt.Size("connections:Q", scale=alt.Scale(range=[50, 500]), legend=None),
        color=alt.value("red"),
        opacity=alt.value(0.85),
        tooltip=[
            alt.Tooltip("title:N", title="Title"),
            alt.Tooltip("author:N", title="Authors"),
            alt.Tooltip("year:N", title="Year"),
            alt.Tooltip("citations_count:N", title="Citations"),
        ]
    )

    _top10_nodes_data["label"] = _top10_nodes_data.apply(
        lambda row: f"{row['author'].split(';')[0].split(',')[0].strip()}, {row['year']}",
        axis=1
    )

    _chart_top10_labels = alt.Chart(_top10_nodes_data).mark_text(fontSize=6, fontWeight="bold").encode(
        x=alt.X("x:Q", axis=None),
        y=alt.Y("y:Q", axis=None),
        text=alt.Text("label:N"),
        color=alt.value("black")
    )

    # Labels layer — cluster number on each node
    _chart_labels = alt.Chart(
        _sample_nodes_data[_sample_nodes_data["cluster_number"] != "No cluster"]
    ).mark_text(fontSize=6, fontWeight="bold").encode(
        x=alt.X("x:Q", axis=None),
        y=alt.Y("y:Q", axis=None),
        text=alt.Text("cluster_number:N"),
        color=alt.value("white")
    )

    # Combined chart — hulls go first (background)
    network_chart5 = (
        _chart_int_edges + _chart_ext_edges + _chart_sample_nodes + _chart_top10_nodes + _chart_labels + _chart_top10_labels
    ).resolve_scale(
        color="independent"
    ).properties(
        title="Citation Network incl. Top 10 Referenced Papers",
        width=700,
        height=500
    ).configure_view(strokeWidth=0)

    network_chart5
    return


@app.cell
def _(df, pd, references_df):
    import networkx as nx
    import numpy as np
    import altair as alt

    # Step 1: Find internal citations (papers that cite each other within the dataset)
    scopus_ids_set = set(references_df["scopus_id"].unique())
    internal_refs = references_df[references_df["cite_to"].isin(scopus_ids_set)].copy()

    # Step 2: Build a directed graph
    G = nx.from_pandas_edgelist(
        internal_refs,
        source="scopus_id",
        target="cite_to",
        create_using=nx.DiGraph()
    )

    # Step 3: Compute layout positions
    pos = nx.spring_layout(G, seed=42, k=1.5)

    # Step 4: Build node dataframe
    node_df = pd.DataFrame([
        {"scopus_id": node, "x": pos[node][0], "y": pos[node][1],
         "degree": G.degree(node)}
        for node in G.nodes()
    ])

    node_df2 = pd.merge(node_df,df, on="scopus_id", how="inner")
    node_df2 = node_df2.rename(columns={"degree": "connections", 
                                        "country of the institution of the first author":"country_institution","place of research (country)":"country_studycase"})

    # Step 5: Build edge dataframe (edges as lines need x/x2, y/y2)
    edge_rows = []
    for src, tgt in G.edges():
        edge_rows.append({
            "x": pos[src][0], "y": pos[src][1],
            "x2": pos[tgt][0], "y2": pos[tgt][1],
            "source": src,
            "target": tgt
        })
    edge_df = pd.DataFrame(edge_rows)


    # Reshape edges so each edge is linked to both its source and target scopus_id
    edge_long_df = pd.concat([
        edge_df.assign(scopus_id=edge_df["source"], role="cited others"),
        edge_df.assign(scopus_id=edge_df["target"], role="was cited")
    ], ignore_index=True)

    # Selection triggered on hover
    hover = alt.selection_point(fields=["scopus_id"], on="mouseover", empty=False)

    edges_chart = alt.Chart(edge_long_df).mark_rule(strokeWidth=1.5).encode(
        x=alt.X("x:Q", axis=None),
        y=alt.Y("y:Q", axis=None),
        x2="x2:Q",
        y2="y2:Q",
        color=alt.condition(
            hover,
            alt.Color("role:N", scale=alt.Scale(
                domain=["cited others", "was cited"],
                range=["red", "green"]
            ), legend=alt.Legend(title="Direction")),
            alt.value("lightgray")
        ),
        opacity=alt.condition(hover, alt.value(0.9), alt.value(0.15)),
        tooltip=[
            alt.Tooltip("source:N", title="Cited by"),
            alt.Tooltip("target:N", title="Cites to")
        ]
    )

    nodes_chart = alt.Chart(node_df2).mark_circle().encode(
        x=alt.X("x:Q", axis=None),
        y=alt.Y("y:Q", axis=None),
        size=alt.Size("connections:Q", scale=alt.Scale(range=[50, 500]), legend=None),
        color=alt.condition(hover, alt.value("orange"), alt.Color("connections:Q", scale=alt.Scale(scheme="viridis"), legend=None)),
        opacity=alt.condition(hover, alt.value(1.0), alt.value(0.7)),
        tooltip=["scopus_id:N", "connections:Q", "Title:N", "Authors:N", "Year:Q", "country_institution:N", "country_study_case:N"]
    ).add_params(hover)


    network_chart = (edges_chart + nodes_chart).properties(
        title="Internal Citation Network",
        width=700,
        height=600
    ).configure_view(strokeWidth=0)

    network_chart
    return alt, edge_df, hover, node_df2, nx


@app.cell
def _(mo, node_df2):
    cluster_options = ["All"] + sorted(node_df2["cluster_number"].dropna().unique().astype(int).tolist())

    cluster_selector = mo.ui.dropdown(
        options=[str(c) for c in cluster_options],
        value="All",
        label="Filter by Cluster"
    )

    cluster_selector
    return (cluster_selector,)


@app.cell
def _(alt, cluster_selector, edge_df, hover, node_df2, pd):
    if cluster_selector.value == "All":
        filtered_nodes = node_df2.copy()
        filtered_nodes["in_cluster"] = True
        _edge_df_filtered = edge_df.copy()
    else:
        cluster_ids = set(node_df2[node_df2["cluster_number"] == int(cluster_selector.value)]["scopus_id"].tolist())

        # Keep edges where AT LEAST ONE endpoint is in the cluster
        mask = edge_df["source"].isin(cluster_ids) | edge_df["target"].isin(cluster_ids)
        _edge_df_filtered = edge_df[mask]

        # All nodes involved in those edges (cluster nodes + their neighbors)
        connected_ids = set(_edge_df_filtered["source"].tolist()) | set(_edge_df_filtered["target"].tolist())

        filtered_nodes = node_df2[node_df2["scopus_id"].isin(connected_ids)].copy()
        filtered_nodes["in_cluster"] = filtered_nodes["scopus_id"].isin(cluster_ids)

    # Rebuild edge_long_df from filtered edges
    _edge_long = pd.concat([
        _edge_df_filtered.assign(scopus_id=_edge_df_filtered["source"], role="cited others"),
        _edge_df_filtered.assign(scopus_id=_edge_df_filtered["target"], role="was cited")
    ], ignore_index=True)

    # Rebuild charts
    _edges = alt.Chart(_edge_long).mark_rule(strokeWidth=1.5).encode(
        x=alt.X("x:Q", axis=None),
        y=alt.Y("y:Q", axis=None),
        x2="x2:Q",
        y2="y2:Q",
        color=alt.condition(
            hover,
            alt.Color("role:N", scale=alt.Scale(
                domain=["cited others", "was cited"],
                range=["red", "green"]
            ), legend=alt.Legend(title="Direction")),
            alt.value("lightgray")
        ),
        opacity=alt.condition(hover, alt.value(0.9), alt.value(0.15)),
        tooltip=[
            alt.Tooltip("source:N", title="Cited by"),
            alt.Tooltip("target:N", title="Cites to")
        ]
    )

    _nodes_in_cluster = alt.Chart(filtered_nodes[filtered_nodes["in_cluster"]]).mark_circle().encode(
        x=alt.X("x:Q", axis=None),
        y=alt.Y("y:Q", axis=None),
        size=alt.Size("connections:Q", scale=alt.Scale(range=[50, 500]), legend=None),
        color=alt.condition(
            hover,
            alt.value("orange"),
            alt.Color("connections:Q", scale=alt.Scale(scheme="viridis"), legend=None)
        ),
        opacity=alt.condition(hover, alt.value(1.0), alt.value(0.85)),
        tooltip=["scopus_id:N", "connections:Q", "Title:N", "Authors:N", "Year:Q", "cluster_number:Q","country_institution:N", "country_study_case:N"]
    )

    _nodes_neighbors = alt.Chart(filtered_nodes[~filtered_nodes["in_cluster"]]).mark_circle().encode(
        x=alt.X("x:Q", axis=None),
        y=alt.Y("y:Q", axis=None),
        size=alt.Size("connections:Q", scale=alt.Scale(range=[50, 500]), legend=None),
        color=alt.condition(hover, alt.value("orange"), alt.value("lightgray")),
        opacity=alt.condition(hover, alt.value(1.0), alt.value(0.4)),
        tooltip=["scopus_id:N", "connections:Q", "Title:N", "Authors:N", "Year:Q", "cluster_number:Q","country_institution:N", "country_study_case:N"]
    )

    network_chart2 = (_edges + _nodes_in_cluster + _nodes_neighbors).add_params(hover).properties(
        title=f"Internal Citation Network — Cluster: {cluster_selector.value}",
        width=700,
        height=600
    ).configure_view(strokeWidth=0)

    network_chart2
    return


@app.cell
def _(node_df2):
    node_df2
    return


@app.cell
def _(mo, node_df2):
    _top10 = node_df2.nlargest(10, "connections")

    top10_options = {
        f"{row['Title'][:50]}... ({row['connections']} connections)": row['scopus_id']
        for _, row in _top10.iterrows()
    }

    top10_selector = mo.ui.dropdown(
        options=top10_options,
        label="Select from Top 10 most connected papers"
    )
    top10_selector
    return (top10_selector,)


@app.cell
def _(alt, edge_df, mo, node_df2, pd, top10_selector):
    mo.stop(top10_selector.value is None, mo.md("Select a paper above to explore its network"))

    _selected_id = top10_selector.value
    _selected_title = node_df2[node_df2["scopus_id"] == _selected_id]["Title"].values[0]

    # Filter edges connected to the selected node
    _mask_top10 = (edge_df["source"] == _selected_id) | (edge_df["target"] == _selected_id)
    _edge_df_top10 = edge_df[_mask_top10]

    # Get all connected nodes (selected + neighbors)
    _connected_ids_top10 = set(_edge_df_top10["source"].tolist()) | set(_edge_df_top10["target"].tolist())
    _nodes_top10 = node_df2[node_df2["scopus_id"].isin(_connected_ids_top10)].copy()
    _nodes_top10["is_selected"] = _nodes_top10["scopus_id"] == _selected_id

    # Rebuild edge long format
    _edge_long_top10 = pd.concat([
        _edge_df_top10.assign(scopus_id=_edge_df_top10["source"], role="cited others"),
        _edge_df_top10.assign(scopus_id=_edge_df_top10["target"], role="was cited")
    ], ignore_index=True)

    hover2 = alt.selection_point(fields=["scopus_id"], on="mouseover", empty=False)

    _edges_top10 = alt.Chart(_edge_long_top10).mark_rule(strokeWidth=1.5).encode(
        x=alt.X("x:Q", axis=None),
        y=alt.Y("y:Q", axis=None),
        x2="x2:Q",
        y2="y2:Q",
        color=alt.condition(
            hover2,
            alt.Color("role:N", scale=alt.Scale(
                domain=["cited others", "was cited"],
                range=["red", "green"]
            ), legend=alt.Legend(title="Direction")),
            alt.value("lightgray")
        ),
        opacity=alt.condition(hover2, alt.value(0.9), alt.value(0.25)),
        tooltip=[
            alt.Tooltip("source:N", title="Cited by"),
            alt.Tooltip("target:N", title="Cites to")
        ]
    )

    # Selected node — highlighted with a black stroke
    _chart_selected_node = alt.Chart(_nodes_top10[_nodes_top10["is_selected"]]).mark_circle(
        stroke="black", strokeWidth=2
    ).encode(
        x=alt.X("x:Q", axis=None),
        y=alt.Y("y:Q", axis=None),
        size=alt.value(400),
        color=alt.value("orange"),
        tooltip=["scopus_id:N", "connections:Q", "Title:N", "Authors:N", "Year:Q", "cluster_number:Q"]
    )

    # Neighbor nodes
    _chart_neighbor_nodes = alt.Chart(_nodes_top10[~_nodes_top10["is_selected"]]).mark_circle().encode(
        x=alt.X("x:Q", axis=None),
        y=alt.Y("y:Q", axis=None),
        size=alt.Size("connections:Q", scale=alt.Scale(range=[50, 400]), legend=None),
        color=alt.condition(
            hover2,
            alt.value("orange"),
            alt.Color("connections:Q", scale=alt.Scale(scheme="viridis"), legend=None)
        ),
        opacity=alt.condition(hover2, alt.value(1.0), alt.value(0.7)),
        tooltip=["scopus_id:N", "connections:Q", "Title:N", "Authors:N", "Year:Q", "cluster_number:Q"]
    )

    network_chart3 = (_edges_top10 + _chart_selected_node + _chart_neighbor_nodes).add_params(hover2).properties(
        title=f"Network of: {_selected_title[:60]}...",
        width=700,
        height=600
    ).configure_view(strokeWidth=0)

    network_chart3
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
