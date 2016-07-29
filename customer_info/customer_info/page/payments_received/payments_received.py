from __future__ import unicode_literals
import frappe
import json
from frappe.utils import flt, cstr, cint
from frappe.utils.csvutils import UnicodeWriter


@frappe.whitelist()
def get_payments_details(customer,from_date,to_date):
	print customer,from_date,to_date

	if customer and from_date and to_date:
		cond = "where customer = '{0}' and (payment_date BETWEEN '{1}' AND '{2}') ".format(customer,from_date,to_date)

	elif customer and from_date:
		cond = "where customer = '{0}' and payment_date >= '{1}'".format(customer,from_date)

	elif customer and to_date:
		cond = "where customer = '{0}' and payment_date < '{1}'".format(customer,to_date)

	elif from_date and to_date:
		cond = "where (payment_date BETWEEN '{0}' AND '{1}') ".format(from_date,to_date)

	elif customer:
		cond = "where customer = '{0}' ".format(customer)

	elif from_date:
		cond = "where payment_date >= '{0}'".format(from_date)

	elif to_date:
		cond = "where payment_date <= '{0}'".format(to_date)

	else:
		cond = ""

	
	return frappe.db.sql("""select payment_date,customer,rental_payment,
								late_fees,receivables,rental_payment+late_fees+receivables as total_payment_received,
								bank_transfer,cash,bank_card,
								balance,discount,bonus,concat(name,'') as refund,payments_ids
								from `tabPayments History` {0}
								where refund = "No"
								order by customer """.format(cond),as_dict=1,debug=1)

def get_child_data(parent):
	return frappe.db.sql("""select payment_id,due_date,total,late_fees,rental_payment
						from `tabPayment History Record` where parent = '{0}' """.format(parent),as_dict=1,debug=1)

@frappe.whitelist()
def set_payments_history_record(record_data,parent):
	data = json.loads(record_data)
	ph_doc = frappe.get_doc("Payments History",parent)
	if len(ph_doc.payment_history_record) == 0:
		for d in data:
			nl = ph_doc.append('payment_history_record', {})
			nl.payment_id = d['payments_id']
			nl.due_date = d['due_date']
			nl.late_fees = d['late_fees']
			nl.rental_payment = d['rental_payment']	
			nl.total = d['total']
		ph_doc.save(ignore_permissions=True)
		return "done"		

@frappe.whitelist()
def create_csv(to_date,from_date,customer):

	w = UnicodeWriter()
	w = add_header(w)
	w = add_data(w, to_date,from_date,customer)
	# write out response as a type csv
	frappe.response['result'] = cstr(w.getvalue())
	frappe.response['type'] = 'csv'
	frappe.response['doctype'] = "Payment Received Report"

def add_header(w):
	w.writerow(["Payment Received Report"])
	return w

def add_data(w,to_date,from_date,customer):
	data = get_payments_details(customer,from_date,to_date)
	if len(data) > 0:
		w.writerow('\n')
		w.writerow(['Payment Received'])
		w.writerow(['', 'Payment Date','Customer', 'Rental Payment','Late Fees','Receivables','Total Rental Payment','Bank Transfer','Cash','Bank Card','Balance','Discount','Bonus'])
		for i in data:
			row = ['', i['payment_date'], i['customer'], i['rental_payment'],i['late_fees'],i['receivables'],i['total_payment_received'],i['bank_transfer'],i['cash'],i['bank_card'],i['balance'],i['discount'],i['bonus']]
			w.writerow(row)	
			w.writerow(['','Payment id','Due Date','Rental Payment','Late Fees','Total'])
			for j in get_child_data(i['refund']):
				row = ['', j['payment_id'],j['due_date'],j['rental_payment'],j['late_fees'],j['total']]
				w.writerow(row)
	return w

	