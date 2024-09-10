from datetime import datetime as d

import pandas as pd
import streamlit as st
from streamlit_gsheets import GSheetsConnection


def main():
	form = st.form("check_in_form")
	form.title("Check In Form")
	email = form.text_input("Email đăng ký")
	submit_btn = form.form_submit_button("Submit")
	if 'state submit' not in st.session_state:
		st.session_state['state submit'] = True

	if submit_btn:
		conn = st.connection("gsheets", type = GSheetsConnection, ttl = 0)
		sign_up_sheet = conn.read(worksheet = "sign_up_sheet", ttl = 0)
		check_in_sheet = conn.read(worksheet = "check_in_sheet", ttl = 0)
		person = sign_up_sheet[sign_up_sheet["Email"] == email]
		if person.empty:
			result = "Bạn chưa đăng ký"
			has_error = True
			check_in_person_df = pd.DataFrame(
				[
					{
						"Tên": "",
						"Email": email,
						"Mã số đồ uống": "",
						"Dấu thời gian": d.now().strftime("%Y-%m-%d %H:%M:%S")
					}
				]
			)
		else:
			print(person["Checked"].values[0])
			if person["Checked"].values[0] == 1:
				check_in_person_df = None
				result = "Email này đã được dùng để check in rồi, xin hãy nhập lại email!"
				has_error = True

			else:
				check_in_person_df = pd.DataFrame(
					[
						{
							"Tên": str(person["Tên"].values[0]),
							"Email": str(person["Email"].values[0]),
							"Mã số đồ uống": str(int(person["Mã số đồ uống"].values[0])),
							"Dấu thời gian": d.now().strftime("%Y-%m-%d %H:%M:%S")
						}
					]
				)
				ma_do_uong = person["Mã số đồ uống"].values[0]
				result = str(int(ma_do_uong))
				has_error = False


		if check_in_person_df is not None:
			with st.spinner("Waiting for it ..."):
				update_data_check_in = pd.concat([check_in_sheet, check_in_person_df], axis = 0)
				conn.update(worksheet = "check_in_sheet", data = update_data_check_in)
				sign_up_sheet.loc[sign_up_sheet["Email"] == email, 'Checked'] = 1
				conn.update(worksheet = "sign_up_sheet", data = sign_up_sheet)

		st.text("submit successfully")
		show_result(result, has_error)
		conn.reset()


@st.dialog("Mã số đồ uống")
def show_result(result = None, isError = 0):
	if isError:
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
			<h1 style="font-family: 'Source Sans Pro', sans-serif;font-size:57px;font-weight:700;margin-bottom:25px; text-align:center;">{result}</h1>
		</div>
		""", unsafe_allow_html = True)


if __name__ == '__main__':
	main()
