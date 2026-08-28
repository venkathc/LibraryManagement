"""Tag and collection management page."""

import pandas as pd
import streamlit as st
from sqlalchemy.orm import Session

from services.catalog_service import CatalogService


def render(session: Session) -> None:
    """Render reusable tag and collection management."""
    st.header("Tags and Collections")
    service = CatalogService(session)
    tags_tab, collections_tab = st.tabs(["Tags", "Collections"])
    with tags_tab:
        with st.form("add_tag_form", clear_on_submit=True):
            name = st.text_input("Tag name")
            submitted = st.form_submit_button("Add tag", type="primary")
        if submitted:
            try:
                service.create_tag(name)
            except ValueError as error:
                st.error(str(error))
            else:
                st.success("Tag added.")
                st.rerun()
        tags = service.list_tags()
        if tags:
            st.dataframe(pd.DataFrame([{"Name": tag.name, "Books": len(tag.books)} for tag in tags]), hide_index=True, use_container_width=True)
            tag_choices = {tag.name: tag.id for tag in tags if not tag.books}
            if tag_choices:
                selected = st.selectbox("Unused tag to delete", tag_choices, key="delete_tag")
                if st.button("Delete unused tag", key="delete_tag_button"):
                    service.delete_tag(tag_choices[selected])
                    st.success("Tag deleted.")
                    st.rerun()
        else:
            st.info("No tags yet.")
    with collections_tab:
        with st.form("add_collection_form", clear_on_submit=True):
            name = st.text_input("Collection name")
            description = st.text_area("Description")
            submitted = st.form_submit_button("Add collection", type="primary")
        if submitted:
            try:
                service.create_collection(name, description)
            except ValueError as error:
                st.error(str(error))
            else:
                st.success("Collection added.")
                st.rerun()
        collections = service.list_collections()
        if collections:
            st.dataframe(pd.DataFrame([{"Name": item.name, "Description": item.description or "", "Books": len(item.books)} for item in collections]), hide_index=True, use_container_width=True)
            collection_choices = {item.name: item.id for item in collections if not item.books}
            if collection_choices:
                selected = st.selectbox("Empty collection to delete", collection_choices, key="delete_collection")
                if st.button("Delete empty collection", key="delete_collection_button"):
                    service.delete_collection(collection_choices[selected])
                    st.success("Collection deleted.")
                    st.rerun()
        else:
            st.info("No collections yet.")
