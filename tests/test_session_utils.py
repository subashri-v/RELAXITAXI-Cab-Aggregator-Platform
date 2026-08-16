from unittest.mock import MagicMock, patch

import src.session_utils as session_utils


def test_remember_session_sets_query_params():
    fake_st = MagicMock()
    fake_st.query_params = {}
    with patch("src.session_utils.st", fake_st):
        session_utils.remember_session("customer", 42)
    assert fake_st.query_params["role"] == "customer"
    assert fake_st.query_params["uid"] == "42"


def test_forget_session_clears_query_params():
    fake_st = MagicMock()
    with patch("src.session_utils.st", fake_st):
        session_utils.forget_session()
    fake_st.query_params.clear.assert_called_once()


def test_goto_forwards_current_query_params():
    fake_st = MagicMock()
    fake_st.query_params = {"role": "driver", "uid": "7"}
    with patch("src.session_utils.st", fake_st):
        session_utils.goto("pages/driver_view.py")
    fake_st.switch_page.assert_called_once_with(
        "pages/driver_view.py", query_params={"role": "driver", "uid": "7"}
    )


def test_restore_session_noop_when_already_logged_in():
    fake_st = MagicMock()
    fake_st.session_state.get.return_value = "customer"
    with patch("src.session_utils.st", fake_st), \
         patch("src.session_utils.get_user_by_id") as mock_get_user:
        session_utils.restore_session()
    mock_get_user.assert_not_called()


def test_restore_session_noop_when_no_query_params():
    fake_st = MagicMock()
    fake_st.session_state.get.return_value = None
    fake_st.query_params.get.return_value = None
    with patch("src.session_utils.st", fake_st), \
         patch("src.session_utils.get_user_by_id") as mock_get_user:
        session_utils.restore_session()
    mock_get_user.assert_not_called()


def test_restore_session_ignores_unknown_role():
    fake_st = MagicMock()
    fake_st.session_state = {}
    fake_st.query_params.get.side_effect = lambda key: {"role": "admin", "uid": "1"}.get(key)
    with patch("src.session_utils.st", fake_st), \
         patch("src.session_utils.get_user_by_id") as mock_get_user:
        session_utils.restore_session()
    mock_get_user.assert_not_called()


def test_restore_session_handles_non_numeric_uid():
    fake_st = MagicMock()
    fake_st.session_state = {}
    fake_st.query_params.get.side_effect = lambda key: {"role": "customer", "uid": "not-a-number"}.get(key)
    with patch("src.session_utils.st", fake_st), \
         patch("src.session_utils.get_user_by_id") as mock_get_user:
        session_utils.restore_session()
    mock_get_user.assert_not_called()


def test_restore_session_rehydrates_from_query_params():
    fake_st = MagicMock()
    fake_st.session_state = {}
    fake_st.query_params.get.side_effect = lambda key: {"role": "driver", "uid": "7"}.get(key)
    with patch("src.session_utils.st", fake_st), \
         patch(
             "src.session_utils.get_user_by_id",
             return_value={"id": 7, "name": "Driver Dan"},
         ) as mock_get_user:
        session_utils.restore_session()

    mock_get_user.assert_called_once_with("drivers", 7)
    assert fake_st.session_state["role"] == "driver"
    assert fake_st.session_state["user_id"] == 7
    assert fake_st.session_state["user_name"] == "Driver Dan"


def test_restore_session_user_not_found_leaves_state_empty():
    fake_st = MagicMock()
    fake_st.session_state = {}
    fake_st.query_params.get.side_effect = lambda key: {"role": "customer", "uid": "99"}.get(key)
    with patch("src.session_utils.st", fake_st), \
         patch("src.session_utils.get_user_by_id", return_value=None):
        session_utils.restore_session()

    assert "role" not in fake_st.session_state
