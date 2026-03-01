import streamlit as st
from app.utils.user_database import user_db
from app.utils.log_util import logger

def render_auth_page():
    """渲染认证页面（登录/注册）"""
    st.title("🎓 文献解读Agent系统")
    st.markdown("### 请登录或注册以继续")
    
    # 创建标签页
    tab1, tab2 = st.tabs(["登录", "注册"])
    
    with tab1:
        render_login_form()
    
    with tab2:
        render_register_form()

def render_login_form():
    """渲染登录表单"""
    st.markdown("#### 登录到您的账户")
    
    with st.form("login_form"):
        username = st.text_input("用户名", key="login_username")
        password = st.text_input("密码", type="password", key="login_password")
        
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            submit = st.form_submit_button("登录", use_container_width=True)
        
        if submit:
            if not username or not password:
                st.error("请输入用户名和密码")
            else:
                # 验证用户
                result = user_db.authenticate_user(username, password)
                
                if result["success"]:
                    # 创建会话
                    session_token = user_db.create_session(result["user"]["id"])
                    
                    # 保存到session state
                    st.session_state["user"] = result["user"]
                    st.session_state["session_token"] = session_token
                    
                    st.success("登录成功！")
                    st.rerun()
                else:
                    st.error(result["message"])

def render_register_form():
    """渲染注册表单"""
    st.markdown("#### 创建新账户")
    
    with st.form("register_form"):
        username = st.text_input("用户名", key="register_username", 
                                help="用户名只能包含字母、数字和下划线")
        email = st.text_input("邮箱", key="register_email")
        password = st.text_input("密码", type="password", key="register_password",
                                help="密码至少6位")
        confirm_password = st.text_input("确认密码", type="password", key="register_confirm_password")
        
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            submit = st.form_submit_button("注册", use_container_width=True)
        
        if submit:
            # 验证输入
            if not username or not email or not password or not confirm_password:
                st.error("请填写所有字段")
            elif not validate_username(username):
                st.error("用户名只能包含字母、数字和下划线，长度3-20位")
            elif not validate_email(email):
                st.error("请输入有效的邮箱地址")
            elif len(password) < 6:
                st.error("密码至少6位")
            elif password != confirm_password:
                st.error("两次输入的密码不一致")
            else:
                # 创建用户
                result = user_db.create_user(username, email, password)
                
                if result["success"]:
                    st.success("注册成功！请登录")
                    st.info("请切换到'登录'标签页进行登录")
                else:
                    st.error(result["message"])

def validate_username(username: str) -> bool:
    """验证用户名"""
    import re
    pattern = r'^[a-zA-Z0-9_]{3,20}$'
    return bool(re.match(pattern, username))

def validate_email(email: str) -> bool:
    """验证邮箱"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def check_auth():
    """检查用户是否已登录"""
    # 检查session state
    if "user" in st.session_state and "session_token" in st.session_state:
        # 验证会话
        user_info = user_db.validate_session(st.session_state["session_token"])
        if user_info:
            return True
        else:
            # 会话无效，清除
            if "user" in st.session_state:
                del st.session_state["user"]
            if "session_token" in st.session_state:
                del st.session_state["session_token"]
            return False
    return False

def logout():
    """登出"""
    if "session_token" in st.session_state:
        user_db.delete_session(st.session_state["session_token"])
    
    # 清除session state
    if "user" in st.session_state:
        del st.session_state["user"]
    if "session_token" in st.session_state:
        del st.session_state["session_token"]
    
    st.rerun()