# tests/mock_streamlit.py
from unittest.mock import MagicMock

# ---- Fake StreamlitStopException ----
class StreamlitStopException(Exception):
    pass

# ---- Create mock streamlit module ----
mock_streamlit = MagicMock()
mock_streamlit.StreamlitStopException = StreamlitStopException

# Common Streamlit methods used in driver_view
for fn in [
    "info",
    "subheader",
    "write",
    "warning",
    "error",
    "success",
    "metric",
    "map",
    "progress",
]:
    setattr(mock_streamlit, fn, MagicMock())

# ---- Mock session state ----
mock_streamlit.session_state = {}

# ---- st.stop ----
mock_streamlit.stop = MagicMock(side_effect=StreamlitStopException)

# ---- st.columns ----
def fake_columns(arg):
    """Return enough mock columns depending on argument count."""
    if isinstance(arg, int):
        return tuple(MagicMock() for _ in range(arg))
    if isinstance(arg, (list, tuple)):
        return tuple(MagicMock() for _ in range(len(arg)))
    return (MagicMock(), MagicMock())

mock_streamlit.columns = MagicMock(side_effect=fake_columns)

# ---- st.write & st.markdown (both used in tests/UI) ----
mock_streamlit.write = MagicMock()
mock_streamlit.markdown = MagicMock()

# ---- st_folium (used for maps) ----
mock_streamlit.st_folium = MagicMock()

# Register module aliases
import sys
sys.modules["mock_streamlit"] = mock_streamlit
sys.modules["streamlit"] = mock_streamlit

