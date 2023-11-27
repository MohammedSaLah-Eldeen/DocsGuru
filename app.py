"""
DocsGuru Application.
"""
# streamlit
import streamlit as st

# langchain
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import FAISS

# project modules
from tools.ingestdocs import ingest_docs, get_available_docs, get_embeddings
from agents.core import chat, format_sources_string


# Application Start
# 0.55, 0.1, 0.35
st.image("logo.jpg")
docs_selection, or_word, docs_new = st.columns([0.6, 0.2, 1], gap="medium")

with docs_selection:
    st.header("Available", anchor=False)
    available_docs = get_available_docs()
    selected_docs = st.selectbox(
        label="Documentations for", options=available_docs.keys(), key="docs_selected"
    )
    if st.session_state["docs_selected"] is not None:
        st.write(f"found in \n{available_docs[selected_docs]}")


with or_word:
    st.header("OR", anchor=False)


with docs_new:
    st.header("New docs", anchor=False)
    docs_name = st.text_input(label="For library/framework", placeholder="langchain")
    docs_link = st.text_input(
        label="Link",
        placeholder="https://api.python.langchain.com/en/latest/api_reference.html",
    )

    btncol1, btncol2 = st.columns([2.2, 1], gap="small")
    with btncol1:
        get = st.button(label="get", type="primary")
    with btncol2:
        update = st.button(label="update", type="secondary")

    if get:
        if docs_name == "" or docs_link == "":
            st.write("please provide inputs")
        else:
            with st.spinner(f"fetching docs for {docs_name}..."):
                try:
                    storepath = ingest_docs(
                        name=docs_name,
                        docsurl=docs_link,
                    )
                    st.write(f"created in \n{storepath}")
                except ValueError:
                    st.write(f"please provide a valid URL !")
    elif update:
        if docs_name == "" or docs_link == "":
            st.write("please provide inputs")
        else:
            with st.spinner(f"fetching docs for {docs_name}..."):
                try:
                    storepath = ingest_docs(
                        name=docs_name, docsurl=docs_link, forced=True
                    )
                    st.write(f"created in \n{storepath}")
                except ValueError:
                    st.write(f"please provide a valid URL !")

if st.session_state["docs_selected"] is None:
    st.divider()
    st.markdown("#### create new docs by providing a name and a docs homepage link")
else:
    st.divider()
    st.write("### All set, let's go !")

    prompt = st.chat_input(
        placeholder=f"Ask DocsGuru on {st.session_state['docs_selected']}"
    )

    if "messages" not in st.session_state:
        st.session_state["messages"] = []

    if prompt:
        with st.spinner("Looking through the docs"):
            embeddings = get_embeddings()
            docstore = FAISS.load_local(
                available_docs[st.session_state["docs_selected"]], embeddings
            )
            response = chat(prompt, docstore, chat_history=st.session_state['messages'])
            # getting sources links
            sources = list(dict.fromkeys([document.metadata["source"] for document in response["source_documents"]]))
            answer = f"{response['answer']} \n\n {format_sources_string(sources)}"

            st.session_state["messages"].append({"role": "user", "content": prompt})
            st.session_state["messages"].append(
                {"role": "assistant", "content": answer}
            )

    for message in st.session_state["messages"]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
