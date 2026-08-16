"""Keep a logged-in user's session alive across a browser refresh.

st.session_state lives only on the current browser connection, so a
refresh (which opens a fresh connection) wipes it. We carry just enough
identity in the URL's query params to re-hydrate session_state from the
database on the next load.
"""
import streamlit as st

from db_utils import get_user_by_id

_ROLE_TO_USER_TYPE = {"customer": "riders", "driver": "drivers"}


def remember_session(role: str, user_id: int) -> None:
    """Call right after a successful login to survive future refreshes."""
    st.query_params["role"] = role
    st.query_params["uid"] = str(user_id)


def forget_session() -> None:
    """Call on sign-out so a refresh doesn't silently log the user back in."""
    st.query_params.clear()


def goto(page: str) -> None:
    """st.switch_page wrapper that forwards the current query params.

    st.switch_page clears all query params on navigation unless told
    otherwise, which would silently undo remember_session() on the very
    next page change. Use this instead of st.switch_page everywhere a
    logged-in user might navigate.
    """
    st.switch_page(page, query_params=dict(st.query_params))


def restore_session() -> None:
    """Re-hydrate session_state from the URL if this is a fresh connection."""
    if st.session_state.get("role") is not None:
        return

    role = st.query_params.get("role")
    uid = st.query_params.get("uid")
    user_type = _ROLE_TO_USER_TYPE.get(role)
    if user_type is None or uid is None:
        return

    try:
        user = get_user_by_id(user_type, int(uid))
    except (TypeError, ValueError):
        return

    if user:
        st.session_state["role"] = role
        st.session_state["user_id"] = user["id"]
        st.session_state["user_name"] = user["name"]
