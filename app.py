import re
from datetime import datetime as d

import pandas as pd
import pytz
import streamlit as st
from streamlit_gsheets import GSheetsConnection


def get_person_by_email(sign_up_sheet, email):
	"""Lấy thông tin của người dùng từ email"""
	return sign_up_sheet[sign_up_sheet["Email"] == email]


def create_check_in_person_df(name, email, phone_number, drink_code, timezone = 'Asia/Ho_Chi_Minh'):
	"""Tạo DataFrame thông tin check-in của người dùng"""
	tz = pytz.timezone(timezone)
	return pd.DataFrame(
		[
			{
				"Email": email,
				"Họ và tên": name,
				"Số điện thoại": phone_number,
				"Mã đồ uống": drink_code,
				"Dấu thời gian": d.now(tz).strftime("%Y-%m-%d %H:%M:%S")
			}
		]
	)


def update_check_in_status(conn, email, sign_up_sheet, check_in_person_df, check_in_sheet):
	"""Cập nhật trạng thái check-in và ghi lại thông tin"""
	with st.spinner("Waiting for it ..."):
		# Cập nhật dữ liệu check-in
		updated_check_in_sheet = pd.concat([check_in_sheet, check_in_person_df], axis = 0)
		conn.update(worksheet = "check_in_sheet", data = updated_check_in_sheet)
		# Đánh dấu email đã check-in
		sign_up_sheet.loc[sign_up_sheet["Email"] == email, 'Checked'] = 1
		conn.update(worksheet = "sign_up_sheet", data = sign_up_sheet)
	st.text("submit successfully")


@st.dialog("Mã số đồ uống")
def show_result(result, is_error):
	"""Hiển thị kết quả sau khi người dùng check-in"""
	if is_error:
		st.markdown(f"""
					<div style="opacity:0.96;margin:auto;padding:10px 20px;">
						<h2 style="text-align:center;">{result}</h2>
					</div>
					""", unsafe_allow_html = True)
	else:
		st.markdown(f"""
		<div style="opacity:0.96;margin:auto;padding:10px 20px;">
			<h2 style="text-align:center;">Bạn đã check in thành công!</h2>
			<h2 style="text-align:center;">Mã số đồ uống của bạn là:</h2>
			<h1 style="font-family: 'Source Sans Pro', sans-serif;font-size:57px;font-weight:700;margin-bottom:25px; text-align:center;">{result[0]}</h1>
			<h2 style="text-align:center;">{result[1]}</h2>
		</div>
		""", unsafe_allow_html = True)


def main():
	with open("style.css") as f:
		css = f.read()

	st.markdown(f'<style>{css}</style>', unsafe_allow_html = True)

	st.markdown("<div><h1 id='check-in-form'>Check In Form</h1></div>", unsafe_allow_html = True)
	with st.form("check_in_form", border = True):

		st.image("AIO_HN.jpg")
		email = st.text_input("Email đăng ký", placeholder = "Email")
		st.divider()
		submit_btn = st.form_submit_button("Submit", type = "primary")
	conn = st.connection("gsheets", type = GSheetsConnection, ttl = 0)
	if 'state_submit' not in st.session_state:
		st.session_state['state_submit'] = True

	if submit_btn:
		if email is None or email == '':
			st.warning("Email không được để trống! Xin mời hãy nhập Email!")
			return

		if not re.match(r"^\S+@\S+\.\S+$", email):
			st.error("Email nhập không đúng định dạng, vui lòng nhập lại Email!")
			return

		sign_up_sheet = conn.read(worksheet = "sign_up_sheet", ttl = 0)
		sign_up_sheet.columns = [column.strip() for column in sign_up_sheet.columns]
		check_in_sheet = conn.read(worksheet = "check_in_sheet", ttl = 0)
		check_in_sheet.columns = [column.strip() for column in check_in_sheet.columns]
		person = get_person_by_email(sign_up_sheet, email)

		if person.empty:
			result = "Bạn chưa đăng ký"
			has_error = True
			check_in_person_df = create_check_in_person_df("", email, "", "")
		else:
			if person["Checked"].values[0] == 1:
				check_in_person_df = None
				result = "Email này đã được dùng để check in rồi, xin hãy nhập lại email!"
				has_error = True
			else:
				name = person["Họ và tên"].values[0]
				email = person["Email"].values[0]
				phone_number = person["Số điện thoại"].values[0]
				drink_code = (str(int(person["Mã đồ uống"].values[0])),person["Tên đồ uống"].values[0])
				check_in_person_df = create_check_in_person_df(name, email, phone_number, drink_code)
				result = drink_code
				has_error = False

		if check_in_person_df is not None:
			update_check_in_status(conn, email, sign_up_sheet, check_in_person_df, check_in_sheet)

		show_result(result, has_error)
		if has_error:
			st.error(result)
		else:
			st.info(f"Mã só đồ uống của bạn là: {result[0]}- {result[1]}")
		conn.reset()


if __name__ == '__main__':
	main()
