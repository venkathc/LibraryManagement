"""Tag and collection management page."""

from html import escape

import streamlit as st
from sqlalchemy.orm import Session

from services.catalog_service import CatalogService
from utils.page_ui import render_page_header


def _styles() -> None:
    st.html("""<style>
    .catalog-title{color:#123c55;font:700 1rem/1.25 'Poppins',sans-serif;margin:0}.catalog-copy{color:#55717b;font:.78rem/1.45 'Poppins',sans-serif;margin:.2rem 0 .85rem}.tag-cloud{display:flex;flex-wrap:wrap;gap:.55rem}.tag-chip{align-items:center;background:#fff;border:1px solid rgba(18,60,85,.12);border-radius:99px;color:#123c55;display:inline-flex;font:600 .78rem/1 'Poppins',sans-serif;gap:.4rem;padding:.5rem .65rem}.tag-dot{border-radius:50%;height:.6rem;width:.6rem}.collection-card{background:linear-gradient(135deg,rgba(247,252,251,.96),#fff);border:1px solid rgba(28,138,131,.2);border-radius:8px;box-shadow:0 6px 18px rgba(18,60,85,.05);min-height:130px;padding:.9rem}.collection-name{color:#123c55;font:700 .95rem/1.25 'Poppins',sans-serif;margin:0}.collection-description{color:#55717b;font:.75rem/1.45 'Poppins',sans-serif;margin:.3rem 0}.collection-count{color:#146c72;font:600 .72rem/1 'Poppins',sans-serif}[data-testid='stMainBlockContainer'] [data-testid='stVerticalBlockBorderWrapper']{border-color:rgba(28,138,131,.22);border-radius:10px}</style>""")


def render(session: Session) -> None:
    """Render reusable tag and collection management."""
    render_page_header("Tags and collections", "Organise the library with reusable labels and purposeful reading shelves.", "T")
    _styles()
    service = CatalogService(session)
    tags_tab, collections_tab = st.tabs(["Tags", "Collections"])
    with tags_tab:
        with st.container(border=True):
            st.html('<p class="catalog-title">Create new tag</p><p class="catalog-copy">Use colours to scan and organise related books quickly.</p>')
            with st.form("add_tag_form", clear_on_submit=True):
                name_column, color_column = st.columns((3, 1))
                name = name_column.text_input("Tag name", placeholder="e.g. Research, Must read")
                color = color_column.color_picker("Tag colour", "#1C8A83")
                description = st.text_input("Description (optional)", placeholder="A short note about this tag")
                submitted = st.form_submit_button("Create tag", type="primary", icon=":material/add:")
        if submitted:
            try:
                service.create_tag(name, color, description)
            except ValueError as error:
                st.error(str(error))
            else:
                st.toast("Tag created.", icon=":material/check_circle:")
                st.rerun()
        tags = service.list_tags()
        if tags:
            st.html('<p class="catalog-title">Your tags</p><p class="catalog-copy">Select a tag below to review its use, or remove unused labels.</p>')
            query = st.text_input("Find a tag", placeholder="Search tags", icon=":material/search:", key="catalog_tag_search")
            visible_tags = [tag for tag in tags if query.casefold() in tag.name.casefold() or query.casefold() in (tag.description or "").casefold()]
            st.html('<div class="tag-cloud">' + "".join(f'<span class="tag-chip"><span class="tag-dot" style="background:{escape(tag.color)}"></span>{escape(tag.name)} <small>({len(tag.books)})</small></span>' for tag in visible_tags) + '</div>')
            if not visible_tags:
                st.caption("No tags match this search.")
            tag_choices = {tag.name: tag.id for tag in tags if not tag.books}
            if tag_choices:
                selected = st.selectbox("Unused tag", tag_choices, key="delete_tag")
                if st.button("Delete unused tag", icon=":material/delete:", key="delete_tag_button"):
                    service.delete_tag(tag_choices[selected])
                    st.toast("Unused tag deleted.", icon=":material/delete:")
                    st.rerun()
        else:
            st.info("No tags yet. Create a tag to make your library easier to browse.", icon=":material/local_offer:")
    with collections_tab:
        with st.container(border=True):
            st.html('<p class="catalog-title">Create collection</p><p class="catalog-copy">Build purposeful shelves for reading lists, topics, and projects.</p>')
            with st.form("add_collection_form", clear_on_submit=True):
                name = st.text_input("Collection name", placeholder="e.g. Programming books")
                description = st.text_area("Description", placeholder="What belongs in this collection?", height=90)
                submitted = st.form_submit_button("Create collection", type="primary", icon=":material/create_new_folder:")
        if submitted:
            try:
                service.create_collection(name, description)
            except ValueError as error:
                st.error(str(error))
            else:
                st.toast("Collection created.", icon=":material/check_circle:")
                st.rerun()
        collections = service.list_collections()
        if collections:
            st.html('<p class="catalog-title">Your collections</p><p class="catalog-copy">Each collection is a reusable shelf that can be assigned from the Add or Edit Book form.</p>')
            for offset in range(0, len(collections), 3):
                for column, item in zip(st.columns(3), collections[offset:offset + 3]):
                    with column:
                        st.html(f'<section class="collection-card"><p class="collection-name">{escape(item.name)}</p><p class="collection-description">{escape(item.description or "No description yet.")}</p><span class="collection-count">{len(item.books)} books</span></section>')
            collection_choices = {item.name: item.id for item in collections if not item.books}
            if collection_choices:
                selected = st.selectbox("Empty collection", collection_choices, key="delete_collection")
                if st.button("Delete empty collection", icon=":material/delete:", key="delete_collection_button"):
                    service.delete_collection(collection_choices[selected])
                    st.toast("Empty collection deleted.", icon=":material/delete:")
                    st.rerun()
        else:
            st.info("No collections yet. Create a shelf for the books you want to group together.", icon=":material/collections_bookmark:")
