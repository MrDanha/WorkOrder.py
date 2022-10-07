import base64
import json
import os
import threading
import time
import tkinter
from configparser import ConfigParser
from datetime import datetime
from tkinter import *
from tkinter import messagebox
from tkinter import simpledialog
from tkinter import ttk
from urllib.parse import quote
import pyodbc
import requests
import urllib3
from ttkthemes import ThemedTk
from ttkwidgets import CheckboxTreeview
from dateutil.relativedelta import *
from multiprocessing import Queue

# Om vi har trial period!
trialperiod = '2030-05-20 07:00:00'
now = str(datetime.now())
if now > trialperiod:
    window1 = ThemedTk(theme="blue")
    window1.geometry("780x715")
    window1.title("WorkOrder")

    Label_trial = Label(window1,
                        text="Trial period is over! \nContact your system provider for more details.",
                        font=("Arial" "Bold", 30))
    Label_trial.grid(row=1, column=1, pady=40, padx=30, columnspan=2)
    window1.mainloop()

# Programmet i sin helhet
else:

    #####

    # FIXA LAGERPLATS ID I NYA COLUMNEN SOM ÄR SKAPAD!

    #####
    # Config-filen med inloggningsuppgifter till Monitor
    file = './config.ini'
    parser = ConfigParser()
    parser.read(file, encoding="UTF-8")

    host = parser["inloggning"]['host']
    company = parser['inloggning']['company']
    username = parser['inloggning']['username']
    password = parser['inloggning']['password']

    ODBC = parser['ODBC']['DSN']

    lagerplats = parser['logics']['lagerplats']
    lagerstalle = parser['logics']['lagerstalle']
    leverantorskod_uthyrning = parser['logics']['leverantorskod_uthyrning']
    artikel_avskrivningstid = parser['logics_EF']['artikel_avskrivningstid']
    artikel_avskrivningskonto = parser['logics_EF']['artikel_avskrivningskonto']
    artikel_tillgangskonto = parser['logics_EF']['artikel_tillgangskonto']
    artikel_rengoring = parser['logics_EF']['artikel_rengoring']
    serienummer_tillgangskonto = parser['logics_EF']['serienummer_tillgangskonto']
    serienummer_avskrivningskonto = parser['logics_EF']['serienummer_avskrivningskonto']
    serienummer_anskaffningsvarde = parser['logics_EF']['serienummer_anskaffningsvarde']
    serienummer_restvarde = parser['logics_EF']['serienummer_restvarde']
    serienummer_avskriven = parser['logics_EF']['serienummer_avskriven']
    serienummer_avskrivningstid = parser['logics_EF']['serienummer_avskrivningstid']
    serienummer_klar = parser['logics_EF']['serienummer_klar']
    serienummer_utrangeratpris = parser['logics_EF']['serienummer_utrangeratpris']
    serienummer_utrangeratdatum = parser['logics_EF']['serienummer_utrangeratdatum']

    artikel_ef = []

    artikel_ef.append(artikel_avskrivningstid)
    artikel_ef.append(artikel_avskrivningskonto)
    artikel_ef.append(artikel_tillgangskonto)
    artikel_ef.append(artikel_rengoring)

    inleverans_ef_sn = []

    inleverans_ef_sn.append(serienummer_tillgangskonto)
    inleverans_ef_sn.append(serienummer_avskrivningskonto)
    inleverans_ef_sn.append(serienummer_anskaffningsvarde)
    inleverans_ef_sn.append(serienummer_restvarde)
    inleverans_ef_sn.append(serienummer_avskrivningstid)
    inleverans_ef_sn.append(serienummer_klar)


    # plockare_EF = parser['logics']['plockare_EF']
    # plockare_EF = json.loads(plockare_EF)

    # Ta bort varning om certifikat
    urllib3.disable_warnings()

    # cnxn = pyodbc.connect(f"DSN={ODBC}")
    # cursor = cnxn.cursor()
    # customer10 = cursor.execute('''create table if not EXISTS ReadOnlyUser.anp_serienummer
    #                                     (
    #                                     Serienummer Numeric(30) NOT NULL,
    #                                     UNIQUE (Serienummer))
    #                                     ''')
    # cursor.commit()
    # cursor.close()
    #
    # cnxn = pyodbc.connect(f"DSN={ODBC}")
    # cursor = cnxn.cursor()
    # customer11 = cursor.execute('''
    # BEGIN IF NOT EXISTS ( SELECT serienummer FROM ReadOnlyUser.anp_serienummer
    #                WHERE serienummer = 900000000 )
    #                BEGIN
    #                INSERT INTO ReadOnlyUser.anp_serienummer (serienummer) VALUES (900000000)
    #                END
    #                END
    #                                         ''')
    # cursor.commit()
    # cursor.close()
    # Skapa tabell för att planera plocklistor

    # Inställningar för skalet
    window = ThemedTk(theme="aquativo")
    window.geometry("930x715")
    window.title("WorkOrder")
    window.grid_columnconfigure(0, weight=0)
    window.iconbitmap('delivery.ico')
    #window.resizable(False, False)
    style = ttk.Style(window)
    style.element_create("Custom.Treeheading.border", "from", "aquativo")
    style.layout("Custom.Treeview.Heading", [
        ("Custom.Treeheading.cell", {'sticky': 'nswe'}),
        ("Custom.Treeheading.border", {'sticky': 'nswe', 'children': [
            ("Custom.Treeheading.padding", {'sticky': 'nswe', 'children': [
                ("Custom.Treeheading.image", {'side': 'right', 'sticky': ''}),
                ("Custom.Treeheading.text", {'sticky': 'we'})
            ]})
        ]}),
    ])
    style.configure("Custom.Treeview.Heading",
                    background="lightblue", foreground="black", relief="sunken")
    style.map("Custom.Treeview.Heading",
              relief=[('active', 'groove'), ('pressed', 'flat')])

    style.configure('my.TButton', font=('Helvetica', 12, "bold"))
    

    tabControl = ttk.Notebook(window)

    dev_plan = ttk.Frame(tabControl)
    tab1 = ttk.Frame(tabControl)
    tab2 = ttk.Frame(tabControl)
    tab3 = ttk.Frame(tabControl)
    tab4 = ttk.Frame(tabControl)
    tab5 = ttk.Frame(tabControl)


    tabControl.add(tab1, text='Inleverans   ')
    tabControl.add(tab2, text='Lagerorder ut')
    tabControl.add(tab3, text='Återlämning  ')
    tabControl.add(tab4, text='Splitta S/N  ')
    # tab1.configure(font=("Calibri", 8))
    tabControl.grid(row=0, column=0)

    # Functions

    # Funktion för markerad rad i rapportera inleveransrutinen, skriver också i Entry-boxes
    def select_record_IL(events):
        try:
            IL_entry_recieve.delete(0, END)
            IL_entry_length.delete(0, END)
            selected = my_tree.selection()[0]
            children = my_tree.item(selected, "values")
            IL_entry_recieve.insert(0, children[3])
            IL_entry_length.insert(0, children[5])
        except Exception as e:
            messagebox.showerror("Error", f"Issues with selecting the record {e}")


    # Funktion för att uppdatera rad i rapportera inleveransrutinen
    def update_record_IL():
        try:
            if IL_entry_recieve.get() != "":
                selected = my_tree.selection()[0]
                children = my_tree.item(selected, "values")
                my_tree.set(selected, "#4", float(IL_entry_recieve.get()))
            if IL_entry_length.get() != "":
                selected = my_tree.selection()[0]
                children = my_tree.item(selected, "values")
                my_tree.set(selected, "#6", int(IL_entry_length.get()))
            IL_entry_recieve.delete(0, END)
            IL_entry_length.delete(0, END)
        except Exception as e:
            messagebox.showerror("Error", f"Issues with updating the record {e}")

    # Funktion för att läsa in orderrader i treeview Rapportera inleverans
    def populate_treeview_recieve(events):
        try:
            for u in my_tree.get_children():
                my_tree.delete(u)
            ordernumber = str(IL_entry_ordernumber.get())
            urllib3.disable_warnings()
            s = requests.session()
            url = f"https://{host}/sv/{company}/login"
            inloggning = \
                {
                    "Username": f"{username}",
                    "Password": f"{password}",
                    "ForceRelogin": True
                }

            def Retry1(s, max_tries=40):
                counter = 0
                while True:
                    # s = requests.session()
                    r = s.post(url=url, json=inloggning, verify=False)
                    if r.status_code == 200:
                        return r
                    counter += 1
                    if counter == max_tries:
                        messagebox.showerror("Error", f'Not able to login to the API')
                        break
                    time.sleep(0.4)

            r = Retry1(s)
            r_fel = r.json()
            if r_fel == None or r_fel == "None":
                messagebox.showerror("Error", f'Not able to login to the API')
            else:
                url_get_rows_PO = f"https://{host}/sv/{company}/api/v1/Purchase/PurchaseOrders?$filter=OrderNumber eq '{ordernumber}' and LifeCycleState eq 10&$expand=Rows, Part"
                def Retry2(s, max_tries=40):
                    counter = 0
                    while True:
                        reportResulst = s.get(url=url_get_rows_PO, verify=False)
                        if reportResulst.status_code == 200:
                            return reportResulst

                        counter += 1
                        if counter == max_tries:
                            messagebox.showerror("Error", f'Not able to fetch the purchase order')
                            break

                        if reportResulst.status_code != 200:
                            r = Retry1(s)
                        time.sleep(0.4)

                po_and_rows = Retry2(s)
                po_and_rows_json = po_and_rows.json()
                if po_and_rows_json == []:
                    messagebox.showerror("Error", f'Not able to fetch the purchase order')
                else:
                    for i in po_and_rows_json[0]["Rows"]:
                        if i["RestQuantity"] <= 0:
                            pass
                        else:
                            part_id = i["PartId"]
                            unit_id = i["UnitId"]
                            url_get_part_info = f"https://{host}/sv/{company}/api/v1/Inventory/Parts?$filter=Id eq {int(part_id)}"

                            def Retry3(s, max_tries=40):
                                counter = 0
                                while True:
                                    reportResulst = s.get(url=url_get_part_info, verify=False)
                                    if reportResulst.status_code == 200:
                                        return reportResulst

                                    counter += 1
                                    if counter == max_tries:
                                        messagebox.showerror("Error", f'Not able to fetch the part information on the parts included in the purchase order')
                                        break

                                    if reportResulst.status_code != 200:
                                        r = Retry1(s)
                                    time.sleep(0.4)

                            part = Retry3(s)
                            part_json = part.json()
                            partnumber = str(part_json[0]["PartNumber"])
                            desc = str(part_json[0]["Description"])

                            url_get_unit_info = f"https://{host}/sv/{company}/api/v1/Common/Units?$filter=Id eq {int(unit_id)}"

                            def Retry4(s, max_tries=40):
                                counter = 0
                                while True:
                                    reportResulst = s.get(url=url_get_unit_info, verify=False)
                                    if reportResulst.status_code == 200:
                                        return reportResulst

                                    counter += 1
                                    if counter == max_tries:
                                        messagebox.showinfo("Error", f'Not able to fetch the part unit information on the parts included in the purchase order')
                                        break

                                    if reportResulst.status_code != 200:
                                        r = Retry1(s)
                                    time.sleep(0.4)

                            unit = Retry4(s)
                            unit_json = unit.json()
                            unit_code = str(unit_json[0]["Code"])
                            restquantity = float(i["RestQuantity"])
                            recieveQ = float(i["RestQuantity"])
                            length = int(i["RowsGoodsLabel"])
                            id = int(i["Id"])
                            price = float(i["PriceInCompanyCurrency"])
                            my_tree.insert('', 'end', values=(partnumber, desc, restquantity, recieveQ, unit_code, length, id, part_id, price))

        except Exception as e:
            messagebox.showerror("Error", f"Issues with populating the treeview {e}")

    # Funktion för att ankomstrapportera
    def report_recieve():
        artikelnummer = []
        benamningar = []
        rest_antal = []
        inleverans_antal = []
        enhet = []
        langder = []
        id = []
        part_id = []
        price = []
        for u in my_tree.get_children():
            children = my_tree.item(u, "values")
            artikelnummer.append(children[0])
            benamningar.append(children[1])
            rest_antal.append(children[2])
            inleverans_antal.append(children[3])
            enhet.append(children[4])
            langder.append(children[5])
            id.append(children[6])
            part_id.append(children[7])
            price.append(children[8])

        urllib3.disable_warnings()
        s = requests.session()
        url = f"https://{host}/sv/{company}/login"
        inloggning = \
            {
                "Username": f"{username}",
                "Password": f"{password}",
                "ForceRelogin": True
            }

        def Retry1(s, max_tries=40):
            counter = 0
            while True:
                # s = requests.session()
                r = s.post(url=url, json=inloggning, verify=False)
                if r.status_code == 200:
                    return r
                counter += 1
                if counter == max_tries:
                    messagebox.showinfo("Error", f'Not able to login to the API')
                    break
                time.sleep(0.4)

        r = Retry1(s)
        r_fel = r.json()
        if r_fel == None or r_fel == "None":
            messagebox.showerror("Error", f'Not able to login to the API')



        else:

            for i, o, p, q, r, t, y in zip(artikelnummer, inleverans_antal, enhet, langder, id, part_id, price):
                ARTAVS = None
                ARTAVK = None
                ARTTIL = None
                ARTREN = None
                for ef_value in artikel_ef:
                    if ef_value == f'{artikel_avskrivningstid}':
                        ef_url = f"https://{host}/sv/{company}/api/v1/Common/ExtraFields?$filter=ParentId eq {t} and Identifier eq '{ef_value}'"

                        def Retry2(s, max_tries=40):
                            counter = 0
                            while True:
                                reportResulst = s.get(url=ef_url, verify=False)
                                if reportResulst.status_code == 200:
                                    return reportResulst

                                counter += 1
                                if counter == max_tries:
                                    messagebox.showinfo("Error1", f'Error find the extra field')
                                    break

                                if reportResulst.status_code != 200:
                                    r = Retry1(s)
                                time.sleep(0.4)

                        ef_result = Retry2(s)
                        ef_result_json = ef_result.json()
                        ARTAVS = int(ef_result_json[0]["IntegerValue"])

                    elif ef_value == f'{artikel_avskrivningskonto}':
                        ef_url = f"https://{host}/sv/{company}/api/v1/Common/ExtraFields?$filter=ParentId eq {t} and Identifier eq '{ef_value}'"

                        def Retry2(s, max_tries=40):
                            counter = 0
                            while True:
                                reportResulst = s.get(url=ef_url, verify=False)
                                if reportResulst.status_code == 200:
                                    return reportResulst

                                counter += 1
                                if counter == max_tries:
                                    messagebox.showinfo("Error2", f'Error find the extra field')
                                    break

                                if reportResulst.status_code != 200:
                                    r = Retry1(s)
                                time.sleep(0.4)

                        ef_result = Retry2(s)
                        ef_result_json = ef_result.json()
                        ARTAVK = int(ef_result_json[0]["IntegerValue"])

                    elif ef_value == f'{artikel_tillgangskonto}':
                        ef_url = f"https://{host}/sv/{company}/api/v1/Common/ExtraFields?$filter=ParentId eq {t} and Identifier eq '{ef_value}'"

                        def Retry2(s, max_tries=40):
                            counter = 0
                            while True:
                                reportResulst = s.get(url=ef_url, verify=False)
                                if reportResulst.status_code == 200:
                                    return reportResulst

                                counter += 1
                                if counter == max_tries:
                                    messagebox.showinfo("Error3", f'Error find the extra field')
                                    break

                                if reportResulst.status_code != 200:
                                    r = Retry1(s)
                                time.sleep(0.4)

                        ef_result = Retry2(s)
                        ef_result_json = ef_result.json()
                        ARTTIL = int(ef_result_json[0]["IntegerValue"])

                    elif ef_value == f'{artikel_rengoring}':
                        ef_url = f"https://{host}/sv/{company}/api/v1/Common/ExtraFields?$filter=ParentId eq {t} and Identifier eq '{ef_value}'"

                        def Retry2(s, max_tries=40):
                            counter = 0
                            while True:
                                reportResulst = s.get(url=ef_url, verify=False)
                                if reportResulst.status_code == 200:
                                    return reportResulst

                                counter += 1
                                if counter == max_tries:
                                    messagebox.showinfo("Error4", f'Error find the extra field')
                                    break

                                if reportResulst.status_code != 200:
                                    r = Retry1(s)
                                time.sleep(0.4)

                        ef_result = Retry2(s)
                        ef_result_json = ef_result.json()
                        ARTREN = str(ef_result_json[0]["StringValue"])

                float_Q = float(o)
                int_Q = int(float_Q)
                # cnxn = pyodbc.connect(f"DSN={ODBC}")
                # cursor = cnxn.cursor()
                # cursor.execute(f"""
                #                        select top 1 serienummer
                #                        from ReadOnlyUser.anp_serienummer
                #                        order by serienummer desc
                #                                                             """)
                #
                # result900 = cursor.fetchall()

                ef_pr = f"https://{host}/sv/{company}/api/v1/Inventory/ProductRecords?$filter=StartsWith(SerialNumber, 'SER9')&$orderby=SerialNumber desc&$top=1"

                def Retry100(s, max_tries=40):
                    counter = 0
                    while True:
                        reportResulst = s.get(url=ef_pr, verify=False)
                        if reportResulst.status_code == 200:
                            return reportResulst

                        counter += 1
                        if counter == max_tries:
                            messagebox.showinfo("Error", f'Not able to find the starting product record')
                            break

                        if reportResulst.status_code != 200:
                            r = Retry1(s)
                        time.sleep(0.4)

                ef_pr = Retry100(s)
                ef_pr_json = ef_pr.json()
                next_serial_number_string = ef_pr_json[0]["SerialNumber"]

                serials = []
                nextserial = int(next_serial_number_string[3:])
                for next in range(int_Q):
                    nextserial += 1
                    serials.append(nextserial)

                serials_end = []
                for i in serials:
                    serial_keys = {
                            "SerialNumber": "SER"+str(i),
                            "Quantity": 1.0
                        }
                    serials_end.append(serial_keys)
                json = {
                    "PurchaseOrderRowId": int(r),
                    "Quantity": float(o),
                    "DeleteFutureRest": False,
                    "Locations": [{
                        "PartLocationName": f"{lagerplats}",
                        "Quantity": float(o),
                        "ProductRecords": serials_end
                    }]
                }
                url_post_arrivals = f"https://{host}/sv/{company}/api/v1/Purchase/PurchaseOrders/ReportArrivals"
                json = {
                        "Rows": [json]
                }
                def Retry2(s, max_tries=40):
                    counter = 0
                    while True:
                        reportResulst = s.post(url=url_post_arrivals, json=json, verify=False)
                        if reportResulst.status_code == 200:
                            return reportResulst

                        counter += 1
                        if counter == max_tries:
                            messagebox.showerror("Error", f'Not able to report arrival on a row on the purchase order, status message: {reportResulst.text}')
                            break

                        if reportResulst.status_code != 200:
                            r = Retry1(s)
                        time.sleep(0.4)

                po_and_rows = Retry2(s)
                po_and_rows_json = po_and_rows.json()
                for i in po_and_rows_json["ProductRecordIds"]:
                    url_product_record_update = f"https://{host}/sv/{company}/api/v1/Inventory/ProductRecords/SetProperties"
                    json_product_record = {
                                          "ProductRecordId": int(i),
                                          "RegistrationNo": {"Value": str(q)}
                                                            }

                    def Retry6(s, max_tries=40):
                        counter = 0
                        while True:
                            reportResulst = s.post(url=url_product_record_update, json=json_product_record, verify=False)
                            if reportResulst.status_code == 200:
                                return reportResulst

                            counter += 1
                            if counter == max_tries:
                                messagebox.showerror("Error", f'Not able to update the charge numbers, since the row has been reported arrival, \nplease update the charge numbers manually')
                                break

                            if reportResulst.status_code != 200:
                                r = Retry1(s)
                            time.sleep(0.4)

                    lista_ef = []

                    for j in inleverans_ef_sn:
                        date_now = datetime.now().date()
                        if j == serienummer_tillgangskonto:
                            lista_ef.append({"Identifier": serienummer_tillgangskonto, "IntegerValue": int(ARTTIL)})
                        elif j == serienummer_avskrivningskonto:
                            lista_ef.append({"Identifier": serienummer_avskrivningskonto, "IntegerValue": int(ARTAVK)})
                        elif j == serienummer_anskaffningsvarde:
                            lista_ef.append({"Identifier": serienummer_anskaffningsvarde, "DecimalValue": float(y)})
                        elif j == serienummer_restvarde:
                            lista_ef.append({"Identifier": serienummer_restvarde, "DecimalValue": float(y)})
                        elif j == serienummer_avskrivningstid:
                            lista_ef.append({"Identifier": serienummer_avskrivningstid, "IntegerValue": int(ARTAVS)})
                        elif j == serienummer_klar:
                            new_date = date_now + relativedelta(months=+int(ARTAVS))
                            lista_ef.append({"Identifier": serienummer_klar, "DateOnlyValue": f"{new_date}"})

                    product_record_update = Retry6(s)
                    product_record_update_json = product_record_update.json()

                    url_ef_value_sn = f"https://{host}/sv/{company}/api/v1/Common/Commands/SetExtraFieldValues"
                    json_ef_values = {
                                      "EntityId": int(i),
                                      "EntityType": 0,
                                      "Values": lista_ef
                                    }

                    def Retry7(s, max_tries=40):
                        counter = 0
                        while True:
                            reportResulst = s.post(url=url_ef_value_sn, json=json_ef_values, verify=False)
                            if reportResulst.status_code == 200:
                                return reportResulst

                            counter += 1
                            if counter == max_tries:
                                messagebox.showerror("Error", f'Was not able to set extra field values on product record id {i}')
                                break

                            if reportResulst.status_code != 200:
                                r = Retry1(s)
                            time.sleep(0.4)

                    ef_values_update = Retry7(s)
                    ef_values_update_json = ef_values_update.json()
        messagebox.showinfo("Info", "Inleveransen gick ok!")
        for u in my_tree.get_children():
            my_tree.delete(u)
        IL_entry_ordernumber.delete(0, END)
        IL_entry_length.delete(0, END)
        IL_entry_recieve.delete(0, END)
        IL_entry_ordernumber.focus_set()

                    # Uppdatera extra fälten på serienummer härnäst

    # tab1: Design Inleverans
    # Label till rapportera inleverans

    IL_label_rutin = ttk.Label(tab1, text="Rapportera Inleverans", font=("Calibri", 18, "bold"))
    IL_label_rutin.grid(row=0, column=0, padx=(10, 0), pady=(2, 20), sticky=W, columnspan=2)

    # Label till ordernummer i rapportera inleverans
    IL_label_ordernumber = ttk.Label(tab1, text="Ordernummer: ", font=("Calibri", 14, "bold"))
    IL_label_ordernumber.grid(row=1, column=0, padx=(10, 0), pady=1, sticky=W)

    # Entry till ordernummer
    IL_entry_ordernumber = ttk.Entry(tab1, font=("Calibri", 14))
    IL_entry_ordernumber.grid(row=2, column=0, padx=(10, 0), pady=(0, 40), sticky=W)
    IL_entry_ordernumber.bind("<Return>", populate_treeview_recieve)

    # Skal till TreeView för att hämta information från plocklista
    tree_frame_plock1 = Frame(tab1)
    tree_frame_plock1.grid(row=3, column=0, sticky=W, columnspan=4, ipady=70, pady=(0, 10), padx=(10, 0))
    tree_scroll_plock1 = ttk.Scrollbar(tree_frame_plock1)
    tree_scroll_plock1.pack(side=RIGHT, fill=Y)
    my_tree = ttk.Treeview(tree_frame_plock1, style="Custom.Treeview", yscrollcommand=tree_scroll_plock1.set)
    my_tree.tag_configure("Test", background="lightgrey", font=('Helvetica', 12, "italic"))
    my_tree.tag_configure("Test1", background="white")
    tree_scroll_plock1.config(command=my_tree.yview)
    my_tree['columns'] = ("Artikelnummer", "Benämning", "Restantal", "Inlevereransantal", "Enhet", "Längd", "ID", "PARTID")
    my_tree['displaycolumns'] = ("Artikelnummer", "Benämning", "Restantal", "Inlevereransantal", "Enhet", "Längd")
    my_tree.column("#0", width=1, minwidth=1, stretch=0)
    my_tree.column("Artikelnummer", anchor=W, width=140)
    my_tree.column("Benämning", anchor=W, width=300)
    my_tree.column("Restantal", anchor=W, width=90)
    my_tree.column("Inlevereransantal", anchor=W, width=180)
    my_tree.column("Enhet", anchor=W, width=90)
    my_tree.column("Längd", anchor=W, width=90)
    my_tree.column("ID", anchor=W, width=90)
    my_tree.column("PARTID", anchor=W, width=90)

    my_tree.heading("#0", text="", anchor=W)
    my_tree.heading("Artikelnummer", text="Artikelnummer", anchor=W)
    my_tree.heading("Benämning", text="Benämning", anchor=W)
    my_tree.heading("Restantal", text="Restantal", anchor=W)
    my_tree.heading("Inlevereransantal", text="Inlevereransantal", anchor=W)
    my_tree.heading("Enhet", text="Enhet", anchor=W)
    my_tree.heading("Längd", text="Längd", anchor=W)
    my_tree.heading("ID", text="ID", anchor=W)
    my_tree.heading("PARTID", text="ID", anchor=W)
    my_tree.pack(fill='both', expand=True)

    IL_label_recieve = ttk.Label(tab1, text="Inleveransantal: ", font=("Calibri", 14, "bold"))
    IL_label_recieve.grid(row=4, column=0, padx=(10, 0), pady=(0, 2), sticky=W)
    IL_entry_recieve = ttk.Entry(tab1, font=("Calibri", 14))
    IL_entry_recieve.grid(row=5, column=0, padx=(10, 0), pady=(0, 50), sticky=W)

    IL_label_length = ttk.Label(tab1, text="Längd: ", font=("Calibri", 14, "bold"))
    IL_label_length.grid(row=4, column=1, padx=(2, 0), pady=(0, 2), sticky=W)
    IL_entry_length = ttk.Entry(tab1, font=("Calibri", 14))
    IL_entry_length.grid(row=5, column=1, padx=(2, 0), pady=(0, 50), sticky=W)



    IL_button_edit = ttk.Button(tab1, text="Uppdatera", style="my.TButton", command=update_record_IL)
    IL_button_edit.grid(row=5, column=2, padx=(2, 0), pady=(0, 50), ipadx=30, sticky=W)
    IL_button_recieve = ttk.Button(tab1, text="Inleverera", style="my.TButton", command=report_recieve)
    IL_button_recieve.grid(row=5, column=3, padx=(2, 0), pady=(0, 50), ipadx=30, sticky=W)



    my_tree.bind('<ButtonRelease-1>', select_record_IL)

    #canvas_lp_11 = Canvas(tab5, width=900, height=80, background='white')
    #canvas_lp_11.grid(row=0, column=1, rowspan=3, columnspan=3, sticky=W, padx=10, pady=10)




    # tab2: Design Utleverans

    # Funktion för att populera treeview utleverans

    def populate_treeview_dispatch(events):
        try:
            for u in my_tree_ul.get_children():
                my_tree_ul.delete(u)
            ordernumber = str(UL_entry_ordernumber.get())
            urllib3.disable_warnings()
            s = requests.session()
            url = f"https://{host}/sv/{company}/login"
            inloggning = \
                {
                    "Username": f"{username}",
                    "Password": f"{password}",
                    "ForceRelogin": True
                }

            def Retry1(s, max_tries=40):
                counter = 0
                while True:
                    # s = requests.session()
                    r = s.post(url=url, json=inloggning, verify=False)
                    if r.status_code == 200:
                        return r
                    counter += 1
                    if counter == max_tries:
                        messagebox.showerror("Error", f'Not able to login to the API')
                        break
                    time.sleep(0.4)

            r = Retry1(s)
            r_fel = r.json()
            if r_fel == None or r_fel == "None":
                messagebox.showerror("Error", f'Not able to login to the API')
            else:
                url_get_rows_PO = f"https://{host}/sv/{company}/api/v1/Sales/CustomerOrders?$filter=OrderNumber eq '{ordernumber}' and LifeCycleState eq 10&$expand=Rows, Part"

                def Retry2(s, max_tries=40):
                    counter = 0
                    while True:
                        reportResulst = s.get(url=url_get_rows_PO, verify=False)
                        if reportResulst.status_code == 200:
                            return reportResulst

                        counter += 1
                        if counter == max_tries:
                            messagebox.showerror("Error", f'Not able to fetch the customer order')
                            break

                        if reportResulst.status_code != 200:
                            r = Retry1(s)
                        time.sleep(0.4)

                po_and_rows = Retry2(s)
                po_and_rows_json = po_and_rows.json()
                if po_and_rows_json == []:
                    messagebox.showerror("Error", f'Not able to fetch the customer order')
                else:
                    for i in po_and_rows_json[0]["Rows"]:
                        if i["RestQuantity"] <= 0:
                            pass
                        else:
                            part_id = i["PartId"]
                            unit_id = i["UnitId"]
                            url_get_part_info = f"https://{host}/sv/{company}/api/v1/Inventory/Parts?$filter=Id eq {int(part_id)}"

                            def Retry3(s, max_tries=40):
                                counter = 0
                                while True:
                                    reportResulst = s.get(url=url_get_part_info, verify=False)
                                    if reportResulst.status_code == 200:
                                        return reportResulst

                                    counter += 1
                                    if counter == max_tries:
                                        messagebox.showerror("Error", f'Not able to fetch the part information on the parts included in the customer order')
                                        break

                                    if reportResulst.status_code != 200:
                                        r = Retry1(s)
                                    time.sleep(0.4)

                            part = Retry3(s)
                            part_json = part.json()
                            partnumber = str(part_json[0]["PartNumber"])
                            desc = str(part_json[0]["Description"])

                            url_get_unit_info = f"https://{host}/sv/{company}/api/v1/Common/Units?$filter=Id eq {int(unit_id)}"

                            def Retry4(s, max_tries=40):
                                counter = 0
                                while True:
                                    reportResulst = s.get(url=url_get_unit_info, verify=False)
                                    if reportResulst.status_code == 200:
                                        return reportResulst

                                    counter += 1
                                    if counter == max_tries:
                                        messagebox.showinfo("Error", f'Not able to fetch the part unit information on the parts included in the customer order')
                                        break

                                    if reportResulst.status_code != 200:
                                        r = Retry1(s)
                                    time.sleep(0.4)

                            unit = Retry4(s)
                            unit_json = unit.json()
                            unit_code = str(unit_json[0]["Code"])
                            restquantity = float(i["RestQuantity"])
                            recieveQ = float(i["RestQuantity"])
                            if not i["AlternatePreparationCode"]:
                                for u in my_tree_ul.get_children():
                                    my_tree_ul.delete(u)
                                messagebox.showerror("Error", f"Issues with populating the treeview one or more rows on the customer order is missing the length")
                                UL_entry_ordernumber.delete(0, END)
                                UL_entry_ordernumber.focus_set()
                                break
                            else:
                                try:
                                    length = int(i["AlternatePreparationCode"])
                                    serial_numbers_w_length = f"https://{host}/sv/{company}/api/v1/Inventory/ProductRecords?$filter=PartId eq {int(part_id)} and RegistrationNo eq '{length}'"

                                    def Retry200(s, max_tries=40):
                                        counter = 0
                                        while True:
                                            reportResulst = s.get(url=serial_numbers_w_length, verify=False)
                                            if reportResulst.status_code == 200:
                                                return reportResulst

                                            counter += 1
                                            if counter == max_tries:
                                                messagebox.showinfo("Error", f'Not able to fetch the serial numbers')
                                                break

                                            if reportResulst.status_code != 200:
                                                r = Retry1(s)
                                            time.sleep(0.4)

                                    serials = Retry200(s)
                                    serials_json = serials.json()
                                    serial_numbers_with_right_length = []
                                    serial_numbers_with_right_length_ids = []
                                    for ior in serials_json:
                                        serial_numbers_with_right_length_ids.append(ior["Id"])
                                        serial_numbers_with_right_length.append(ior["SerialNumber"])
                                    if not serial_numbers_with_right_length_ids:
                                        recieveQ = 0
                                        id = int(i["Id"])
                                        my_tree_ul.insert('', 'end', values=(partnumber, desc, restquantity, recieveQ, unit_code, length, id, part_id))
                                    else:
                                        quantity_of_serials = []
                                        for j in serial_numbers_with_right_length_ids:

                                            serial_numbers_Q = f"https://{host}/sv/{company}/api/v1/Inventory/PartLocationProductRecords?$filter=ProductRecordId eq {int(j)}"

                                            def Retry300(s, max_tries=40):
                                                counter = 0
                                                while True:
                                                    reportResulst = s.get(url=serial_numbers_Q, verify=False)
                                                    if reportResulst.status_code == 200:
                                                        return reportResulst

                                                    counter += 1
                                                    if counter == max_tries:
                                                        messagebox.showinfo("Error", f'Not able to fetch the stock balance on the serial numbers')
                                                        break

                                                    if reportResulst.status_code != 200:
                                                        r = Retry1(s)
                                                    time.sleep(0.4)

                                            serials_Q = Retry300(s)
                                            serials_Q_json = serials_Q.json()
                                            quantity_of_serials.append(float(serials_Q_json[0]["Quantity"]))
                                        sum_stock = float(sum(quantity_of_serials))
                                        if recieveQ >= sum_stock:
                                            recieveQ = sum_stock
                                        id = int(i["Id"])
                                        my_tree_ul.insert('', 'end', values=(partnumber, desc, restquantity, recieveQ, unit_code, length, id, part_id))
                                except Exception as e:
                                    for u in my_tree_ul.get_children():
                                        my_tree_ul.delete(u)
                                    messagebox.showerror("Error", f"Issues with converting the length on at least one row")
                                    UL_entry_ordernumber.delete(0, END)
                                    UL_entry_ordernumber.focus_set()


        except Exception as e:
            messagebox.showerror("Error", f"Issues with populating the treeview {e}")

    # Funktion för markerad rad i rapportera utleveransrutinen, skriver också i Entry-boxes
    def select_record_UL(events):
        try:
            UL_entry_recieve.delete(0, END)

            selected = my_tree_ul.selection()[0]
            children = my_tree_ul.item(selected, "values")
            UL_entry_recieve.insert(0, children[3])
        except Exception as e:
            messagebox.showerror("Error", f"Issues with selecting the record {e}")

    # Funktion för att uppdatera rad i rapportera utleveransrutinen
    def update_record_UL():
        try:
            if UL_entry_recieve.get() != "":
                selected = my_tree_ul.selection()[0]
                children = my_tree_ul.item(selected, "values")
                my_tree_ul.set(selected, "#4", float(UL_entry_recieve.get()))
            UL_entry_recieve.delete(0, END)
        except Exception as e:
            messagebox.showerror("Error", f"Issues with updating the record {e}")

        # Funktion för att ankomstrapportera
    def report_dispatch():
        artikelnummer = []
        benamningar = []
        rest_antal = []
        inleverans_antal = []
        enhet = []
        langder = []
        id = []
        part_id = []
        for u in my_tree_ul.get_children():
            children = my_tree_ul.item(u, "values")
            artikelnummer.append(children[0])
            benamningar.append(children[1])
            rest_antal.append(children[2])
            inleverans_antal.append(children[3])
            enhet.append(children[4])
            langder.append(children[5])
            id.append(children[6])
            part_id.append(children[7])

        urllib3.disable_warnings()
        s = requests.session()
        url = f"https://{host}/sv/{company}/login"
        inloggning = \
            {
                "Username": f"{username}",
                "Password": f"{password}",
                "ForceRelogin": True
            }

        def Retry1(s, max_tries=40):
            counter = 0
            while True:
                # s = requests.session()
                r = s.post(url=url, json=inloggning, verify=False)
                if r.status_code == 200:
                    return r
                counter += 1
                if counter == max_tries:
                    messagebox.showinfo("Error", f'Not able to login to the API')
                    break
                time.sleep(0.4)

        r = Retry1(s)
        r_fel = r.json()
        if r_fel == None or r_fel == "None":
            messagebox.showerror("Error", f'Not able to login to the API')



        else:
            for i, o, p, q, r, t in zip(artikelnummer, inleverans_antal, enhet, langder, id, part_id):
                float_Q = float(o)
                int_Q = int(float_Q)
                langd = str(q)
                partid = int(t)
                if int_Q <= 0:
                    pass
                else:
                    serial_numbers_w_length = f"https://{host}/sv/{company}/api/v1/Inventory/ProductRecords?$filter=PartId eq {int(partid)} and RegistrationNo eq '{langd}'&$orderby=ActualArrivalDate desc"

                    def Retry200(s, max_tries=40):
                        counter = 0
                        while True:
                            reportResulst = s.get(url=serial_numbers_w_length, verify=False)
                            if reportResulst.status_code == 200:
                                return reportResulst

                            counter += 1
                            if counter == max_tries:
                                messagebox.showinfo("Error", f'Not able to fetch the serial numbers')
                                break

                            if reportResulst.status_code != 200:
                                r = Retry1(s)
                            time.sleep(0.4)

                    serials = Retry200(s)
                    serials_json = serials.json()
                    serial_numbers_with_right_length = []
                    serial_numbers_with_right_length_ids = []
                    for i in serials_json:
                        serial_numbers_with_right_length_ids.append(i["Id"])
                        serial_numbers_with_right_length.append(i["SerialNumber"])
                    if not serial_numbers_with_right_length_ids:
                        messagebox.showinfo("Error", f'Issues with dispatch report one row on the order since the program did not find any product records')
                    else:
                        quantity_of_serials = []
                        id_of_serials = []
                        location_ids = []
                        for j in serial_numbers_with_right_length_ids:

                            serial_numbers_Q = f"https://{host}/sv/{company}/api/v1/Inventory/PartLocationProductRecords?$filter=ProductRecordId eq {int(j)}"

                            def Retry300(s, max_tries=40):
                                counter = 0
                                while True:
                                    reportResulst = s.get(url=serial_numbers_Q, verify=False)
                                    if reportResulst.status_code == 200:
                                        return reportResulst

                                    counter += 1
                                    if counter == max_tries:
                                        messagebox.showinfo("Error", f'Not able to fetch the stock balance on the serial numbers')
                                        break

                                    if reportResulst.status_code != 200:
                                        r = Retry1(s)
                                    time.sleep(0.4)

                            serials_Q = Retry300(s)
                            serials_Q_json = serials_Q.json()
                            if float(serials_Q_json[0]["Quantity"]) > 0:
                                id_of_serials.append(int(j))
                                quantity_of_serials.append(float(serials_Q_json[0]["Quantity"]))
                                location_ids.append(int(serials_Q_json[0]["PartLocationId"]))
                        serials_end = []
                        for idor, xdor, loc in zip(id_of_serials[:(int_Q)], quantity_of_serials[:(int_Q)], location_ids[:(int_Q)]):
                            serial_keys = {
                                "ProductRecordId": int(idor),
                                "PartLocationId": int(loc),
                                "Quantity": 1.0
                            }
                            serials_end.append(serial_keys)
                        rows = [
                            {
                                "CustomerOrderRowId": int(r),
                                "Quantity": float(int_Q),
                                "DeleteFutureRest": False,
                                "Locations": serials_end
                            }
                        ]
                        url_post_departure = f"https://{host}/sv/{company}/api/v1/Sales/CustomerOrders/ReportDeliveries"
                        json_dep = {
                            "Rows": rows
                        }

                        def Retry500(s, max_tries=40):
                            counter = 0
                            while True:
                                reportResulst = s.post(url=url_post_departure, json=json_dep, verify=False)
                                if reportResulst.status_code == 200:
                                    return reportResulst

                                counter += 1
                                if counter == max_tries:
                                    messagebox.showerror("Error", f'Not able to report dispatch on a row on the customer order, status message: {reportResulst.text}')
                                    break

                                if reportResulst.status_code != 200:
                                    r = Retry1(s)
                                time.sleep(0.4)

                        co_and_rows = Retry500(s)
                        co_and_rows_json = co_and_rows.json()
                        if co_and_rows.status_code == 200:
                            co_url_arrival = f"https://{host}/sv/{company}/api/v1/Sales/CustomerOrders?$filter=OrderNumber eq '{str(UL_entry_ordernumber.get())}'&$expand=PurchaseOrder"

                            def Retry800(s, max_tries=40):
                                counter = 0
                                while True:
                                    reportResulst = s.get(url=co_url_arrival, verify=False)
                                    if reportResulst.status_code == 200:
                                        return reportResulst

                                    counter += 1
                                    if counter == max_tries:
                                        messagebox.showinfo("Error", f'Not able to get the customer order for arrival reporting')
                                        break

                                    if reportResulst.status_code != 200:
                                        r = Retry1(s)
                                    time.sleep(0.4)

                            co_know = Retry800(s)
                            co_know_json = co_know.json()
                            purchase_ordernumber = str(co_know_json[0]["PurchaseOrder"]["OrderNumber"])
                            active_customer_del_address_id = int(co_know_json[0]["ActiveDeliveryAddressCustomerId"])

                            cust_id = f"https://{host}/sv/{company}/api/v1/Sales/Customers?$filter=Id eq {active_customer_del_address_id}"

                            def Retry1000(s, max_tries=40):
                                counter = 0
                                while True:
                                    reportResulst = s.get(url=cust_id, verify=False)
                                    if reportResulst.status_code == 200:
                                        return reportResulst

                                    counter += 1
                                    if counter == max_tries:
                                        messagebox.showerror("Error", f'Not able to fetch the purchase order')
                                        break

                                    if reportResulst.status_code != 200:
                                        r = Retry1(s)
                                    time.sleep(0.4)

                            cust_cust = Retry1000(s)
                            cust_cust_json = cust_cust.json()
                            stock_location = str(cust_cust_json[0]["Code"])

                            url_get_rows_PO = f"https://{host}/sv/{company}/api/v1/Purchase/PurchaseOrders?$filter=OrderNumber eq '{purchase_ordernumber}' and LifeCycleState eq 10&$expand=Rows, Part"

                            def Retry2(s, max_tries=40):
                                counter = 0
                                while True:
                                    reportResulst = s.get(url=url_get_rows_PO, verify=False)
                                    if reportResulst.status_code == 200:
                                        return reportResulst

                                    counter += 1
                                    if counter == max_tries:
                                        messagebox.showerror("Error", f'Not able to fetch the purchase order')
                                        break

                                    if reportResulst.status_code != 200:
                                        r = Retry1(s)
                                    time.sleep(0.4)

                            po_and_rows = Retry2(s)
                            po_and_rows_json = po_and_rows.json()
                            if po_and_rows_json == []:
                                messagebox.showerror("Error", f'Not able to fetch the purchase order')
                            else:
                                for ioren in po_and_rows_json[0]["Rows"]:
                                    if int(ioren["LinkedStockOrderRowId"]) == int(r):
                                        json_1 = {
                                            "PurchaseOrderRowId": int(ioren["Id"]),
                                            "Quantity": float(len(co_and_rows_json["ProductRecordIds"])),
                                            "DeleteFutureRest": False,
                                            "Locations": [{
                                                "PartLocationName": f"{stock_location}",
                                                "Quantity": float(len(co_and_rows_json["ProductRecordIds"]))#,
                                                #"ProductRecords": serials_do_keys
                                            }]
                                        }
                                        url_post_arrivals = f"https://{host}/sv/{company}/api/v1/Purchase/PurchaseOrders/ReportArrivals"
                                        json = {
                                            "Rows": [json_1]
                                        }

                                        def Retry2(s, max_tries=40):
                                            counter = 0
                                            while True:
                                                reportResulst = s.post(url=url_post_arrivals, json=json, verify=False)
                                                if reportResulst.status_code == 200:
                                                    return reportResulst

                                                counter += 1
                                                if counter == max_tries:
                                                    messagebox.showerror("Error", f'Not able to report arrival on a row on the purchase order, status message: {reportResulst.text}')
                                                    break

                                                if reportResulst.status_code != 200:
                                                    r = Retry1(s)
                                                time.sleep(0.4)

                                        po_and_rows = Retry2(s)
                                        po_and_rows_json = po_and_rows.json()
                                    else:
                                        pass


        messagebox.showinfo("Info", "Utleveransen gick ok!")
        for u in my_tree_ul.get_children():
            my_tree_ul.delete(u)
        UL_entry_ordernumber.delete(0, END)
        UL_entry_recieve.delete(0, END)
        UL_entry_ordernumber.focus_set()

        # Uppdatera extra fälten på serienummer härnäst

    UL_label_rutin = ttk.Label(tab2, text="Utleverera lagerorder", font=("Calibri", 18, "bold"))
    UL_label_rutin.grid(row=0, column=0, padx=(10, 0), pady=(2, 20), sticky=W, columnspan=2)

    # Label till ordernummer i rapportera inleverans
    UL_label_ordernumber = ttk.Label(tab2, text="Ordernummer: ", font=("Calibri", 14, "bold"))
    UL_label_ordernumber.grid(row=1, column=0, padx=(10, 0), pady=1, sticky=W)

    # Entry till ordernummer
    UL_entry_ordernumber = ttk.Entry(tab2, font=("Calibri", 14))
    UL_entry_ordernumber.grid(row=2, column=0, padx=(10, 0), pady=(0, 40), sticky=W)
    UL_entry_ordernumber.bind("<Return>", populate_treeview_dispatch)

    # Skal till TreeView för att hämta information från plocklista
    tree_frame_UL = Frame(tab2)
    tree_frame_UL.grid(row=3, column=0, sticky=W, columnspan=4, ipady=70, pady=(0, 10), padx=(10, 0))
    tree_scroll_UL = ttk.Scrollbar(tree_frame_UL)
    tree_scroll_UL.pack(side=RIGHT, fill=Y)
    my_tree_ul = ttk.Treeview(tree_frame_UL, style="Custom.Treeview", yscrollcommand=tree_scroll_UL.set)
    my_tree_ul.tag_configure("Test", background="lightgrey", font=('Helvetica', 12, "italic"))
    my_tree_ul.tag_configure("Test1", background="white")
    tree_scroll_UL.config(command=my_tree_ul.yview)
    my_tree_ul['columns'] = ("Artikelnummer", "Benämning", "Restantal", "Utleveransantal", "Enhet", "Längd", "ID", "PARTID", "PRICE")
    my_tree_ul['displaycolumns'] = ("Artikelnummer", "Benämning", "Restantal", "Utleveransantal", "Enhet", "Längd")
    my_tree_ul.column("#0", width=1, minwidth=1, stretch=0)
    my_tree_ul.column("Artikelnummer", anchor=W, width=140)
    my_tree_ul.column("Benämning", anchor=W, width=300)
    my_tree_ul.column("Restantal", anchor=W, width=90)
    my_tree_ul.column("Utleveransantal", anchor=W, width=180)
    my_tree_ul.column("Enhet", anchor=W, width=90)
    my_tree_ul.column("Längd", anchor=W, width=90)
    my_tree_ul.column("ID", anchor=W, width=90)
    my_tree_ul.column("PARTID", anchor=W, width=90)
    my_tree_ul.column("PRICE", anchor=W, width=90)

    my_tree_ul.heading("#0", text="", anchor=W)
    my_tree_ul.heading("Artikelnummer", text="Artikelnummer", anchor=W)
    my_tree_ul.heading("Benämning", text="Benämning", anchor=W)
    my_tree_ul.heading("Restantal", text="Restantal", anchor=W)
    my_tree_ul.heading("Utleveransantal", text="Utleveransantal", anchor=W)
    my_tree_ul.heading("Enhet", text="Enhet", anchor=W)
    my_tree_ul.heading("Längd", text="Längd", anchor=W)
    my_tree_ul.heading("ID", text="ID", anchor=W)
    my_tree_ul.heading("PARTID", text="ID", anchor=W)
    my_tree_ul.heading("PRICE", text="PRICE", anchor=W)
    my_tree_ul.pack(fill='both', expand=True)

    UL_label_recieve = ttk.Label(tab2, text="Utleveransantal: ", font=("Calibri", 14, "bold"))
    UL_label_recieve.grid(row=4, column=0, padx=(10, 0), pady=(0, 2), sticky=W)
    UL_entry_recieve = ttk.Entry(tab2, font=("Calibri", 14))
    UL_entry_recieve.grid(row=5, column=0, padx=(10, 0), pady=(0, 50), sticky=W)

    # UL_label_length = ttk.Label(tab2, text="Längd: ", font=("Calibri", 14, "bold"))
    # UL_label_length.grid(row=4, column=1, padx=(2, 0), pady=(0, 2), sticky=W)
    # UL_entry_length = ttk.Entry(tab2, font=("Calibri", 14))
    # UL_entry_length.grid(row=5, column=1, padx=(2, 0), pady=(0, 50), sticky=W)

    UL_button_edit = ttk.Button(tab2, text="Uppdatera", style="my.TButton", command=update_record_UL)
    UL_button_edit.grid(row=5, column=2, padx=(2, 0), pady=(0, 50), ipadx=30, sticky=W)
    UL_button_recieve = ttk.Button(tab2, text="Utleverera", style="my.TButton", command=report_dispatch)
    UL_button_recieve.grid(row=5, column=3, padx=(2, 0), pady=(0, 50), ipadx=30, sticky=W)

    my_tree_ul.bind('<ButtonRelease-1>', select_record_UL)


    # tab3: Design Återlämning

    # Funktion för att populera treeview utleverans

    def populate_treeview_AL(events):
        try:
            for u in my_tree_AL.get_children():
                my_tree_AL.delete(u)
            ordernumber = str(AL_entry_ordernumber.get())
            urllib3.disable_warnings()
            s = requests.session()
            url = f"https://{host}/sv/{company}/login"
            inloggning = \
                {
                    "Username": f"{username}",
                    "Password": f"{password}",
                    "ForceRelogin": True
                }

            def Retry1(s, max_tries=40):
                counter = 0
                while True:
                    # s = requests.session()
                    r = s.post(url=url, json=inloggning, verify=False)
                    if r.status_code == 200:
                        return r
                    counter += 1
                    if counter == max_tries:
                        messagebox.showerror("Error", f'Not able to login to the API')
                        break
                    time.sleep(0.4)

            r = Retry1(s)
            r_fel = r.json()
            if r_fel == None or r_fel == "None":
                messagebox.showerror("Error", f'Not able to login to the API')
            else:


                wh_url = f"https://{host}/sv/{company}/api/v1/Common/Warehouses?$filter=Code eq '{lagerstalle}'"

                def Retry2(s, max_tries=40):
                    counter = 0
                    while True:
                        reportResulst = s.get(url=wh_url, verify=False)
                        if reportResulst.status_code == 200:
                            return reportResulst

                        counter += 1
                        if counter == max_tries:
                            messagebox.showerror("Error", f'Not able to fetch the warehouse')
                            break

                        if reportResulst.status_code != 200:
                            r = Retry1(s)
                        time.sleep(0.4)

                wh_get = Retry2(s)
                wh_get_json = wh_get.json()
                if wh_get_json == []:
                    messagebox.showerror("Error", f'Not able to fetch the warehouse')
                else:
                    wh_id = int(wh_get_json[0]["Id"])

                    pl_url = f"https://{host}/sv/{company}/api/v1/Inventory/PartLocations?$filter=WarehouseId eq {wh_id} and Name eq '{ordernumber}' and LifeCycleState eq 10 and Balance gt 0&$expand=PartLocationProductRecords"

                    def Retry900(s, max_tries=40):
                        counter = 0
                        while True:
                            reportResulst = s.get(url=pl_url, verify=False)
                            if reportResulst.status_code == 200:
                                return reportResulst

                            counter += 1
                            if counter == max_tries:
                                messagebox.showerror("Error", f'Not able to fetch the part information on the parts included in the customer order')
                                break

                            if reportResulst.status_code != 200:
                                r = Retry1(s)
                            time.sleep(0.4)

                    pl_get = Retry900(s)
                    if pl_get == []:
                        messagebox.showerror("Error", f'Did not find any rows for the specific project')
                    else:
                        pl_get_json = pl_get.json()
                        for pr_bals in pl_get_json:
                            for iora in pr_bals["PartLocationProductRecords"]:
                                if iora["Quantity"] > 0:
                                    #print(iora)
                                    pr_url = f"https://{host}/sv/{company}/api/v1/Inventory/ProductRecords?$filter=Id eq {iora['ProductRecordId']}"

                                    def Retry10000(s, max_tries=40):
                                        counter = 0
                                        while True:
                                            reportResulst = s.get(url=pr_url, verify=False)
                                            if reportResulst.status_code == 200:
                                                return reportResulst

                                            counter += 1
                                            if counter == max_tries:
                                                messagebox.showerror("Error", f'Not able to fetch information regarding the productrecord')
                                                break

                                            if reportResulst.status_code != 200:
                                                r = Retry1(s)
                                            time.sleep(0.4)

                                    pr_get = Retry10000(s)
                                    pr_get_json = pr_get.json()
                                    part_id = int(pr_get_json[0]["PartId"])
                                    part_url = f"https://{host}/sv/{company}/api/v1/Inventory/Parts?$filter=Id eq {part_id}"

                                    def Retry10001(s, max_tries=40):
                                        counter = 0
                                        while True:
                                            reportResulst = s.get(url=part_url, verify=False)
                                            if reportResulst.status_code == 200:
                                                return reportResulst

                                            counter += 1
                                            if counter == max_tries:
                                                messagebox.showerror("Error", f'Not able to fetch information regarding the productrecord')
                                                break

                                            if reportResulst.status_code != 200:
                                                r = Retry1(s)
                                            time.sleep(0.4)

                                    part_get = Retry10001(s)
                                    part_get_json = part_get.json()

                                    my_tree_AL.insert('', 'end', values=(0, pr_get_json[0]["SerialNumber"], part_get_json[0]["PartNumber"], part_get_json[0]["Description"], pr_get_json[0]["RegistrationNo"], pr_get_json[0]["RegistrationNo"], 0, part_id, iora['ProductRecordId'], iora["Quantity"], iora["PartLocationId"]))



        except Exception as e:
            messagebox.showerror("Error", f"Issues with populating the treeview {e}")


    # Funktion för markerad rad i rapportera utleveransrutinen, skriver också i Entry-boxes
    def select_record_AL(events):
        try:
            AL_entry_recieve.delete(0, END)

            selected = my_tree_AL.selection()[0]
            children = my_tree_AL.item(selected, "values")
            AL_entry_recieve.insert(0, children[5])
            var.set(int(children[0]))
            var2.set(int(children[6]))
        except Exception as e:
            messagebox.showerror("Error", f"Issues with selecting the record {e}")


    # Funktion för att uppdatera rad i rapportera utleveransrutinen
    def update_record_UL():
        try:
            if AL_entry_recieve.get() != "":
                selected = my_tree_AL.selection()[0]
                children = my_tree_AL.item(selected, "values")
                my_tree_AL.set(selected, "#6", int(AL_entry_recieve.get()))
                my_tree_AL.set(selected, "#1", int(var.get()))
                my_tree_AL.set(selected, "#7", int(var2.get()))
            AL_entry_recieve.delete(0, END)
            var.set(0)
            var2.set(0)
        except Exception as e:
            messagebox.showerror("Error", f"Issues with updating the record {e}")

        # Funktion för att ankomstrapportera


    def create_invoice():
        # my_tree_AL.column("Återlämna", anchor=W, width=100)
        # my_tree_AL.column("Serienummer", anchor=W, width=130)
        # my_tree_AL.column("Artikelnr.", anchor=W, width=110)
        # my_tree_AL.column("Benämning", anchor=W, width=230)
        # my_tree_AL.column("Uthyrd längd", anchor=W, width=110)
        # my_tree_AL.column("Återl. längd", anchor=W, width=110)
        # my_tree_AL.column("Rengör", anchor=W, width=90)
        # my_tree_AL.column("PARTID", anchor=W, width=90)
        # my_tree_AL.column("PR_ID", anchor=W, width=90)
        # my_tree_AL.column("QUANTITY", anchor=W, width=90)
        # my_tree_AL.column("PL_ID", anchor=W, width=90)
        aterlamna = []
        serienummer = []
        artnr = []
        ben = []
        uthyrd = []
        ater = []
        rengor = []
        partid = []
        pr_id = []
        quantity = []
        pl_id = []
        for u in my_tree_AL.get_children():
            children = my_tree_AL.item(u, "values")
            aterlamna.append(children[0])
            serienummer.append(children[1])
            artnr.append(children[2])
            ben.append(children[3])
            uthyrd.append(children[4])
            ater.append(children[5])
            rengor.append(children[6])
            partid.append(children[7])
            pr_id.append(children[8])
            quantity.append(children[9])
            pl_id.append(children[10])
        urllib3.disable_warnings()
        s = requests.session()
        url = f"https://{host}/sv/{company}/login"
        inloggning = \
            {
                "Username": f"{username}",
                "Password": f"{password}",
                "ForceRelogin": True
            }

        def Retry1(s, max_tries=40):
            counter = 0
            while True:
                # s = requests.session()
                r = s.post(url=url, json=inloggning, verify=False)
                if r.status_code == 200:
                    return r
                counter += 1
                if counter == max_tries:
                    messagebox.showinfo("Error", f'Not able to login to the API')
                    break
                time.sleep(0.4)

        r = Retry1(s)
        r_fel = r.json()
        if r_fel == None or r_fel == "None":
            messagebox.showerror("Error", f'Not able to login to the API')



        else:
            for var_aterlamna, var_serienummer, var_artnr, var_ben, var_uthyrd, var_ater, var_rengor, var_partid, var_pr_id, var_quantity, var_pl_id in zip(aterlamna, serienummer, artnr, ben, uthyrd, ater, rengor, partid, pr_id, quantity, pl_id):
                if var_aterlamna == 1:

                    purchase_ordertype_url = f"https://{host}/sv/{company}/api/v1/Purchase/PurchaseOrderTypes?$filter=Number eq 3"

                    def Retry2(s, max_tries=40):
                        counter = 0
                        while True:
                            reportResulst = s.get(url=purchase_ordertype_url, verify=False)
                            if reportResulst.status_code == 200:
                                return reportResulst

                            counter += 1
                            if counter == max_tries:
                                messagebox.showerror("Error", f'Not able to fetch the warehouse')
                                break

                            if reportResulst.status_code != 200:
                                r = Retry1(s)
                            time.sleep(0.4)

                    pur_ordertype_get = Retry2(s)
                    pur_ordertype_get_json = pur_ordertype_get.json()
                    purchase_ordertype_id = int(pur_ordertype_get_json[0]["Id"])
                    supplier_url = f"https://{host}/sv/{company}/api/v1/Purchase/Suppliers?$filter=SupplierCode eq '{leverantorskod_uthyrning}'"

                    def Retry2(s, max_tries=40):
                        counter = 0
                        while True:
                            reportResulst = s.get(url=supplier_url, verify=False)
                            if reportResulst.status_code == 200:
                                return reportResulst

                            counter += 1
                            if counter == max_tries:
                                messagebox.showerror("Error", f'Not able to fetch the warehouse')
                                break

                            if reportResulst.status_code != 200:
                                r = Retry1(s)
                            time.sleep(0.4)

                    supplier_get = Retry2(s)
                    supplier_get_json = supplier_get.json()
                    supplier_code = int(supplier_get_json[0]["Id"])

                    #TODO: först hämta extra fält på ursprungligt serienummer, kan lika gärna göra det jämt

                    # serienummer_tillgangskonto = parser['logics_EF']['serienummer_tillgangskonto']
                    # serienummer_avskrivningskonto = parser['logics_EF']['serienummer_avskrivningskonto']
                    # serienummer_anskaffningsvarde = parser['logics_EF']['serienummer_anskaffningsvarde']
                    # serienummer_restvarde = parser['logics_EF']['serienummer_restvarde']
                    # serienummer_avskriven = parser['logics_EF']['serienummer_avskriven']
                    # serienummer_avskrivningstid = parser['logics_EF']['serienummer_avskrivningstid']
                    # serienummer_klar = parser['logics_EF']['serienummer_klar']
                    # serienummer_utrangeratpris = parser['logics_EF']['serienummer_utrangeratpris']
                    # serienummer_utrangeratdatum = parser['logics_EF']['serienummer_utrangeratdatum']

                    SERTILLG = None
                    SERAVSKR = None
                    SERANSKA = None
                    SERRESTV = None
                    SERAVSKREN = None
                    SERAVSTID = None
                    SERKLAR = None
                    SERUTRANG = None
                    SERUTRANGD = None
                    for ef_value in inleverans_ef_sn:
                        if ef_value == f'{serienummer_tillgangskonto}':
                            ef_url = f"https://{host}/sv/{company}/api/v1/Common/ExtraFields?$filter=ParentId eq {var_pr_id} and Identifier eq '{ef_value}'"

                            def Retry2(s, max_tries=40):
                                counter = 0
                                while True:
                                    reportResulst = s.get(url=ef_url, verify=False)
                                    if reportResulst.status_code == 200:
                                        return reportResulst

                                    counter += 1
                                    if counter == max_tries:
                                        messagebox.showinfo("Error1", f'Error find the extra field')
                                        break

                                    if reportResulst.status_code != 200:
                                        r = Retry1(s)
                                    time.sleep(0.4)

                            ef_result = Retry2(s)
                            if ef_result == []:
                                pass
                            else:
                                ef_result_json = ef_result.json()
                                SERTILLG = int(ef_result_json[0]["IntegerValue"])
                        elif ef_value == f'{serienummer_avskrivningskonto}':
                            ef_url = f"https://{host}/sv/{company}/api/v1/Common/ExtraFields?$filter=ParentId eq {var_pr_id} and Identifier eq '{ef_value}'"

                            def Retry2(s, max_tries=40):
                                counter = 0
                                while True:
                                    reportResulst = s.get(url=ef_url, verify=False)
                                    if reportResulst.status_code == 200:
                                        return reportResulst

                                    counter += 1
                                    if counter == max_tries:
                                        messagebox.showinfo("Error2", f'Error find the extra field')
                                        break

                                    if reportResulst.status_code != 200:
                                        r = Retry1(s)
                                    time.sleep(0.4)

                            ef_result = Retry2(s)
                            if ef_result == []:
                                pass
                            else:
                                ef_result_json = ef_result.json()
                                SERAVSKR = int(ef_result_json[0]["IntegerValue"])
                        elif ef_value == f'{serienummer_anskaffningsvarde}':
                            ef_url = f"https://{host}/sv/{company}/api/v1/Common/ExtraFields?$filter=ParentId eq {var_pr_id} and Identifier eq '{ef_value}'"

                            def Retry2(s, max_tries=40):
                                counter = 0
                                while True:
                                    reportResulst = s.get(url=ef_url, verify=False)
                                    if reportResulst.status_code == 200:
                                        return reportResulst

                                    counter += 1
                                    if counter == max_tries:
                                        messagebox.showinfo("Error2", f'Error find the extra field')
                                        break

                                    if reportResulst.status_code != 200:
                                        r = Retry1(s)
                                    time.sleep(0.4)

                            ef_result = Retry2(s)
                            if ef_result == []:
                                pass
                            else:
                                ef_result_json = ef_result.json()
                                SERANSKA = float(ef_result_json[0]["DecimalValue"])
                        elif ef_value == f'{serienummer_restvarde}':
                            ef_url = f"https://{host}/sv/{company}/api/v1/Common/ExtraFields?$filter=ParentId eq {var_pr_id} and Identifier eq '{ef_value}'"

                            def Retry2(s, max_tries=40):
                                counter = 0
                                while True:
                                    reportResulst = s.get(url=ef_url, verify=False)
                                    if reportResulst.status_code == 200:
                                        return reportResulst

                                    counter += 1
                                    if counter == max_tries:
                                        messagebox.showinfo("Error2", f'Error find the extra field')
                                        break

                                    if reportResulst.status_code != 200:
                                        r = Retry1(s)
                                    time.sleep(0.4)

                            ef_result = Retry2(s)
                            if ef_result == []:
                                pass
                            else:
                                ef_result_json = ef_result.json()
                                SERRESTV = float(ef_result_json[0]["DecimalValue"])
                        elif ef_value == f'{serienummer_avskriven}':
                            ef_url = f"https://{host}/sv/{company}/api/v1/Common/ExtraFields?$filter=ParentId eq {var_pr_id} and Identifier eq '{ef_value}'"

                            def Retry2(s, max_tries=40):
                                counter = 0
                                while True:
                                    reportResulst = s.get(url=ef_url, verify=False)
                                    if reportResulst.status_code == 200:
                                        return reportResulst

                                    counter += 1
                                    if counter == max_tries:
                                        messagebox.showinfo("Error2", f'Error find the extra field')
                                        break

                                    if reportResulst.status_code != 200:
                                        r = Retry1(s)
                                    time.sleep(0.4)

                            ef_result = Retry2(s)
                            if ef_result == []:
                                pass
                            else:
                                ef_result_json = ef_result.json()
                                SERAVSKREN = str(ef_result_json[0]["StringValue"])
                        elif ef_value == f'{serienummer_avskrivningstid}':
                            ef_url = f"https://{host}/sv/{company}/api/v1/Common/ExtraFields?$filter=ParentId eq {var_pr_id} and Identifier eq '{ef_value}'"

                            def Retry2(s, max_tries=40):
                                counter = 0
                                while True:
                                    reportResulst = s.get(url=ef_url, verify=False)
                                    if reportResulst.status_code == 200:
                                        return reportResulst

                                    counter += 1
                                    if counter == max_tries:
                                        messagebox.showinfo("Error2", f'Error find the extra field')
                                        break

                                    if reportResulst.status_code != 200:
                                        r = Retry1(s)
                                    time.sleep(0.4)

                            ef_result = Retry2(s)
                            if ef_result == []:
                                pass
                            else:
                                ef_result_json = ef_result.json()
                                SERAVSTID = int(ef_result_json[0]["IntegerValue"])
                        elif ef_value == f'{serienummer_klar}':
                            ef_url = f"https://{host}/sv/{company}/api/v1/Common/ExtraFields?$filter=ParentId eq {var_pr_id} and Identifier eq '{ef_value}'"

                            def Retry2(s, max_tries=40):
                                counter = 0
                                while True:
                                    reportResulst = s.get(url=ef_url, verify=False)
                                    if reportResulst.status_code == 200:
                                        return reportResulst

                                    counter += 1
                                    if counter == max_tries:
                                        messagebox.showinfo("Error2", f'Error find the extra field')
                                        break

                                    if reportResulst.status_code != 200:
                                        r = Retry1(s)
                                    time.sleep(0.4)

                            ef_result = Retry2(s)
                            if ef_result == []:
                                pass
                            else:
                                ef_result_json = ef_result.json()
                                SERKLAR = (ef_result_json[0]["DateOnlyValue"])
                                SERKLAR = str(SERKLAR[0:10])
                        elif ef_value == f'{serienummer_utrangeratpris}':
                            ef_url = f"https://{host}/sv/{company}/api/v1/Common/ExtraFields?$filter=ParentId eq {var_pr_id} and Identifier eq '{ef_value}'"

                            def Retry2(s, max_tries=40):
                                counter = 0
                                while True:
                                    reportResulst = s.get(url=ef_url, verify=False)
                                    if reportResulst.status_code == 200:
                                        return reportResulst

                                    counter += 1
                                    if counter == max_tries:
                                        messagebox.showinfo("Error2", f'Error find the extra field')
                                        break

                                    if reportResulst.status_code != 200:
                                        r = Retry1(s)
                                    time.sleep(0.4)

                            ef_result = Retry2(s)
                            if ef_result == []:
                                pass
                            else:
                                ef_result_json = ef_result.json()
                                SERUTRANG = float(ef_result_json[0]["DecimalValue"])
                        elif ef_value == f'{serienummer_utrangeratdatum}':
                            ef_url = f"https://{host}/sv/{company}/api/v1/Common/ExtraFields?$filter=ParentId eq {var_pr_id} and Identifier eq '{ef_value}'"

                            def Retry2(s, max_tries=40):
                                counter = 0
                                while True:
                                    reportResulst = s.get(url=ef_url, verify=False)
                                    if reportResulst.status_code == 200:
                                        return reportResulst

                                    counter += 1
                                    if counter == max_tries:
                                        messagebox.showinfo("Error2", f'Error find the extra field')
                                        break

                                    if reportResulst.status_code != 200:
                                        r = Retry1(s)
                                    time.sleep(0.4)

                            ef_result = Retry2(s)
                            if ef_result == []:
                                pass
                            else:
                                ef_result_json = ef_result.json()
                                SERUTRANGD = (ef_result_json[0]["DateOnlyValue"])
                                SERUTRANGD = str(SERUTRANGD[0:10])

                    #TODO: sedan skapa nytt serienummer om det diffar i längd
                    #TODO: lägg till gamla och nya fält på det nya serienumret
                    #TODO: uppdatera det gamla serienumret
                    #TODO: gör array från if och else
                    #TODO: skapa I-order och inleverera mot grundlagerstället
                    #TODO: skapa fakturaunderlag på rätt bitar
                else:
                    pass
            #     float_Q = float(o)
            #     int_Q = int(float_Q)
            #     langd = str(q)
            #     partid = int(t)
            #     if int_Q <= 0:
            #         pass
            #     else:
            #         serial_numbers_w_length = f"https://{host}/sv/{company}/api/v1/Inventory/ProductRecords?$filter=PartId eq {int(partid)} and RegistrationNo eq '{langd}'&$orderby=ActualArrivalDate desc"
            #
            #         def Retry200(s, max_tries=40):
            #             counter = 0
            #             while True:
            #                 reportResulst = s.get(url=serial_numbers_w_length, verify=False)
            #                 if reportResulst.status_code == 200:
            #                     return reportResulst
            #
            #                 counter += 1
            #                 if counter == max_tries:
            #                     messagebox.showinfo("Error", f'Not able to fetch the serial numbers')
            #                     break
            #
            #                 if reportResulst.status_code != 200:
            #                     r = Retry1(s)
            #                 time.sleep(0.4)
            #
            #         serials = Retry200(s)
            #         serials_json = serials.json()
            #         serial_numbers_with_right_length = []
            #         serial_numbers_with_right_length_ids = []
            #         for i in serials_json:
            #             serial_numbers_with_right_length_ids.append(i["Id"])
            #             serial_numbers_with_right_length.append(i["SerialNumber"])
            #         if not serial_numbers_with_right_length_ids:
            #             messagebox.showinfo("Error", f'Issues with dispatch report one row on the order since the program did not find any product records')
            #         else:
            #             quantity_of_serials = []
            #             id_of_serials = []
            #             location_ids = []
            #             for j in serial_numbers_with_right_length_ids:
            #
            #                 serial_numbers_Q = f"https://{host}/sv/{company}/api/v1/Inventory/PartLocationProductRecords?$filter=ProductRecordId eq {int(j)}"
            #
            #                 def Retry300(s, max_tries=40):
            #                     counter = 0
            #                     while True:
            #                         reportResulst = s.get(url=serial_numbers_Q, verify=False)
            #                         if reportResulst.status_code == 200:
            #                             return reportResulst
            #
            #                         counter += 1
            #                         if counter == max_tries:
            #                             messagebox.showinfo("Error", f'Not able to fetch the stock balance on the serial numbers')
            #                             break
            #
            #                         if reportResulst.status_code != 200:
            #                             r = Retry1(s)
            #                         time.sleep(0.4)
            #
            #                 serials_Q = Retry300(s)
            #                 serials_Q_json = serials_Q.json()
            #                 if float(serials_Q_json[0]["Quantity"]) > 0:
            #                     id_of_serials.append(int(j))
            #                     quantity_of_serials.append(float(serials_Q_json[0]["Quantity"]))
            #                     location_ids.append(int(serials_Q_json[0]["PartLocationId"]))
            #             serials_end = []
            #             for idor, xdor, loc in zip(id_of_serials[:(int_Q)], quantity_of_serials[:(int_Q)], location_ids[:(int_Q)]):
            #                 serial_keys = {
            #                     "ProductRecordId": int(idor),
            #                     "PartLocationId": int(loc),
            #                     "Quantity": 1.0
            #                 }
            #                 serials_end.append(serial_keys)
            #             rows = [
            #                 {
            #                     "CustomerOrderRowId": int(r),
            #                     "Quantity": float(int_Q),
            #                     "DeleteFutureRest": False,
            #                     "Locations": serials_end
            #                 }
            #             ]
            #             url_post_departure = f"https://{host}/sv/{company}/api/v1/Sales/CustomerOrders/ReportDeliveries"
            #             json_dep = {
            #                 "Rows": rows
            #             }
            #
            #             def Retry500(s, max_tries=40):
            #                 counter = 0
            #                 while True:
            #                     reportResulst = s.post(url=url_post_departure, json=json_dep, verify=False)
            #                     if reportResulst.status_code == 200:
            #                         return reportResulst
            #
            #                     counter += 1
            #                     if counter == max_tries:
            #                         messagebox.showerror("Error", f'Not able to report dispatch on a row on the customer order, status message: {reportResulst.text}')
            #                         break
            #
            #                     if reportResulst.status_code != 200:
            #                         r = Retry1(s)
            #                     time.sleep(0.4)
            #
            #             co_and_rows = Retry500(s)
            #             co_and_rows_json = co_and_rows.json()
            #             if co_and_rows.status_code == 200:
            #                 co_url_arrival = f"https://{host}/sv/{company}/api/v1/Sales/CustomerOrders?$filter=OrderNumber eq '{str(UL_entry_ordernumber.get())}'&$expand=PurchaseOrder"
            #
            #                 def Retry800(s, max_tries=40):
            #                     counter = 0
            #                     while True:
            #                         reportResulst = s.get(url=co_url_arrival, verify=False)
            #                         if reportResulst.status_code == 200:
            #                             return reportResulst
            #
            #                         counter += 1
            #                         if counter == max_tries:
            #                             messagebox.showinfo("Error", f'Not able to get the customer order for arrival reporting')
            #                             break
            #
            #                         if reportResulst.status_code != 200:
            #                             r = Retry1(s)
            #                         time.sleep(0.4)
            #
            #                 co_know = Retry800(s)
            #                 co_know_json = co_know.json()
            #                 purchase_ordernumber = str(co_know_json[0]["PurchaseOrder"]["OrderNumber"])
            #                 active_customer_del_address_id = int(co_know_json[0]["ActiveDeliveryAddressCustomerId"])
            #
            #                 cust_id = f"https://{host}/sv/{company}/api/v1/Sales/Customers?$filter=Id eq {active_customer_del_address_id}"
            #
            #                 def Retry1000(s, max_tries=40):
            #                     counter = 0
            #                     while True:
            #                         reportResulst = s.get(url=cust_id, verify=False)
            #                         if reportResulst.status_code == 200:
            #                             return reportResulst
            #
            #                         counter += 1
            #                         if counter == max_tries:
            #                             messagebox.showerror("Error", f'Not able to fetch the purchase order')
            #                             break
            #
            #                         if reportResulst.status_code != 200:
            #                             r = Retry1(s)
            #                         time.sleep(0.4)
            #
            #                 cust_cust = Retry1000(s)
            #                 cust_cust_json = cust_cust.json()
            #                 stock_location = str(cust_cust_json[0]["Code"])
            #
            #                 url_get_rows_PO = f"https://{host}/sv/{company}/api/v1/Purchase/PurchaseOrders?$filter=OrderNumber eq '{purchase_ordernumber}' and LifeCycleState eq 10&$expand=Rows, Part"
            #
            #                 def Retry2(s, max_tries=40):
            #                     counter = 0
            #                     while True:
            #                         reportResulst = s.get(url=url_get_rows_PO, verify=False)
            #                         if reportResulst.status_code == 200:
            #                             return reportResulst
            #
            #                         counter += 1
            #                         if counter == max_tries:
            #                             messagebox.showerror("Error", f'Not able to fetch the purchase order')
            #                             break
            #
            #                         if reportResulst.status_code != 200:
            #                             r = Retry1(s)
            #                         time.sleep(0.4)
            #
            #                 po_and_rows = Retry2(s)
            #                 po_and_rows_json = po_and_rows.json()
            #                 if po_and_rows_json == []:
            #                     messagebox.showerror("Error", f'Not able to fetch the purchase order')
            #                 else:
            #                     for ioren in po_and_rows_json[0]["Rows"]:
            #                         if int(ioren["LinkedStockOrderRowId"]) == int(r):
            #                             json_1 = {
            #                                 "PurchaseOrderRowId": int(ioren["Id"]),
            #                                 "Quantity": float(len(co_and_rows_json["ProductRecordIds"])),
            #                                 "DeleteFutureRest": False,
            #                                 "Locations": [{
            #                                     "PartLocationName": f"{stock_location}",
            #                                     "Quantity": float(len(co_and_rows_json["ProductRecordIds"]))  # ,
            #                                     # "ProductRecords": serials_do_keys
            #                                 }]
            #                             }
            #                             url_post_arrivals = f"https://{host}/sv/{company}/api/v1/Purchase/PurchaseOrders/ReportArrivals"
            #                             json = {
            #                                 "Rows": [json_1]
            #                             }
            #
            #                             def Retry2(s, max_tries=40):
            #                                 counter = 0
            #                                 while True:
            #                                     reportResulst = s.post(url=url_post_arrivals, json=json, verify=False)
            #                                     if reportResulst.status_code == 200:
            #                                         return reportResulst
            #
            #                                     counter += 1
            #                                     if counter == max_tries:
            #                                         messagebox.showerror("Error", f'Not able to report arrival on a row on the purchase order, status message: {reportResulst.text}')
            #                                         break
            #
            #                                     if reportResulst.status_code != 200:
            #                                         r = Retry1(s)
            #                                     time.sleep(0.4)
            #
            #                             po_and_rows = Retry2(s)
            #                             po_and_rows_json = po_and_rows.json()
            #                         else:
            #                             pass

        messagebox.showinfo("Info", "Utleveransen gick ok!")
        for u in my_tree_ul.get_children():
            my_tree_ul.delete(u)
        UL_entry_ordernumber.delete(0, END)
        UL_entry_recieve.delete(0, END)
        UL_entry_ordernumber.focus_set()

        # Uppdatera extra fälten på serienummer härnäst


    AL_label_rutin = ttk.Label(tab3, text="Projektnummer", font=("Calibri", 18, "bold"))
    AL_label_rutin.grid(row=0, column=0, padx=(10, 0), pady=(2, 20), sticky=W, columnspan=2)

    # Label till ordernummer i rapportera inleverans
    AL_label_ordernumber = ttk.Label(tab3, text="Ordernummer: ", font=("Calibri", 14, "bold"))
    AL_label_ordernumber.grid(row=1, column=0, padx=(10, 0), pady=1, sticky=W)

    # Entry till ordernummer
    AL_entry_ordernumber = ttk.Entry(tab3, font=("Calibri", 14))
    AL_entry_ordernumber.grid(row=2, column=0, padx=(10, 0), pady=(0, 40), sticky=W)
    AL_entry_ordernumber.bind("<Return>", populate_treeview_AL)

    # Skal till TreeView för att hämta information från plocklista
    #part_id, iora['ProductRecordId'], iora["Quantity"], iora["PartLocationId"])
    tree_frame_AL = Frame(tab3)
    tree_frame_AL.grid(row=3, column=0, sticky=W, columnspan=4, ipady=70, pady=(0, 10), padx=(10, 0))
    tree_scroll_AL = ttk.Scrollbar(tree_frame_AL)
    tree_scroll_AL.pack(side=RIGHT, fill=Y)
    my_tree_AL = ttk.Treeview(tree_frame_AL, style="Custom.Treeview", yscrollcommand=tree_scroll_AL.set)
    my_tree_AL.tag_configure("Test", background="lightgrey", font=('Helvetica', 12, "italic"))
    my_tree_AL.tag_configure("Test1", background="white")
    tree_scroll_AL.config(command=my_tree_AL.yview)
    my_tree_AL['columns'] = ("Återlämna", "Serienummer", "Artikelnr.", "Benämning", "Uthyrd längd", "Återl. längd", "Rengör", "PARTID", "PR_ID", "QUANTITY", "PL_ID")
    my_tree_AL['displaycolumns'] = ("Återlämna", "Serienummer", "Artikelnr.", "Benämning", "Uthyrd längd", "Återl. längd", "Rengör")
    my_tree_AL.column("#0", width=1, minwidth=1, stretch=0)
    my_tree_AL.column("Återlämna", anchor=W, width=100)
    my_tree_AL.column("Serienummer", anchor=W, width=130)
    my_tree_AL.column("Artikelnr.", anchor=W, width=110)
    my_tree_AL.column("Benämning", anchor=W, width=230)
    my_tree_AL.column("Uthyrd längd", anchor=W, width=110)
    my_tree_AL.column("Återl. längd", anchor=W, width=110)
    my_tree_AL.column("Rengör", anchor=W, width=90)
    my_tree_AL.column("PARTID", anchor=W, width=90)
    my_tree_AL.column("PR_ID", anchor=W, width=90)
    my_tree_AL.column("QUANTITY", anchor=W, width=90)
    my_tree_AL.column("PL_ID", anchor=W, width=90)

    my_tree_AL.heading("#0", text="", anchor=W)
    my_tree_AL.heading("Återlämna", text="Återlämna", anchor=W)
    my_tree_AL.heading("Serienummer", text="Serienummer", anchor=W)
    my_tree_AL.heading("Artikelnr.", text="Artikelnr", anchor=W)
    my_tree_AL.heading("Benämning", text="Benämning", anchor=W)
    my_tree_AL.heading("Uthyrd längd", text="Uthyrd längd", anchor=W)
    my_tree_AL.heading("Återl. längd", text="Återl. längd", anchor=W)
    my_tree_AL.heading("Rengör", text="Rengör", anchor=W)
    my_tree_AL.heading("PARTID", text="PARTID", anchor=W)
    my_tree_AL.heading("PR_ID", text="PR_ID", anchor=W)
    my_tree_AL.heading("QUANTITY", text="QUANTITY", anchor=W)
    my_tree_AL.heading("PL_ID", text="PL_ID", anchor=W)
    my_tree_AL.pack(fill='both', expand=True)

    AL_label_recieve = ttk.Label(tab3, text="Återlämnad längd: ", font=("Calibri", 14, "bold"))
    AL_label_recieve.grid(row=4, column=0, padx=(10, 0), pady=(0, 2), sticky=W)
    AL_entry_recieve = ttk.Entry(tab3, font=("Calibri", 14))
    AL_entry_recieve.grid(row=5, column=0, padx=(10, 0), pady=(0, 50), sticky=W)

    var = IntVar(value=0)
    var2 = IntVar(value=0)
    c1 = ttk.Checkbutton(tab3, text='Återlämna', onvalue=1, offvalue=0, variable=var)
    c1.grid(row=4, column=1, padx=(10, 0), pady=(0, 2), sticky=S+W)
    #c1.bind('<ButtonRelease-1>', get_state)
    c2 = ttk.Checkbutton(tab3, text='Rengör', onvalue=1, offvalue=0, variable=var2)
    c2.grid(row=5, column=1, padx=(10, 0), pady=(0, 2), sticky=N+W)

    # UL_label_length = ttk.Label(tab2, text="Längd: ", font=("Calibri", 14, "bold"))
    # UL_label_length.grid(row=4, column=1, padx=(2, 0), pady=(0, 2), sticky=W)
    # UL_entry_length = ttk.Entry(tab2, font=("Calibri", 14))
    # UL_entry_length.grid(row=5, column=1, padx=(2, 0), pady=(0, 50), sticky=W)

    AL_button_edit = ttk.Button(tab3, text="Uppdatera", style="my.TButton", command=update_record_UL)
    AL_button_edit.grid(row=5, column=2, padx=(2, 0), pady=(0, 50), ipadx=30, sticky=W)
    AL_button_recieve = ttk.Button(tab3, text="Utleverera", style="my.TButton", command=create_invoice)
    AL_button_recieve.grid(row=5, column=3, padx=(2, 0), pady=(0, 50), ipadx=30, sticky=W)

    my_tree_AL.bind('<ButtonRelease-1>', select_record_AL)





    # Skal till TreeView för att hämta information från om lagerplats
    # my_tree_lp123 = ttk.Treeview(tab5, columns=(
    # "Artikelnummer", "Benämning", "Restkvantitet", "Batch/Serienr", "PL_ID", "PR_ID", "PART_ID", "GS1_CODE",
    # "Lagerplats", "EF_VALUE"), displaycolumns=("Artikelnummer", "Benämning", "Restkvantitet", "Lagerplats"))
    # my_tree_lp123.column("#0", width=0, stretch=NO)
    # my_tree_lp123.column("Artikelnummer", anchor=W, width=90)
    # my_tree_lp123.column("Benämning", anchor=W, width=150)
    # my_tree_lp123.column("Restkvantitet", anchor=W, width=60)
    # my_tree_lp123.column("Batch/Serienr", anchor=W, width=60)
    # my_tree_lp123.column("PL_ID", anchor=W, width=60)
    # my_tree_lp123.column("PR_ID", anchor=W, width=60)
    # my_tree_lp123.column("PART_ID", anchor=W, width=60)
    # my_tree_lp123.column("GS1_CODE", anchor=W, width=60)
    # my_tree_lp123.column("Lagerplats", anchor=W, width=60)
    # my_tree_lp123.column("EF_VALUE", anchor=W, width=60)
    #
    # my_tree_lp123.heading("#0", text="", anchor=W)
    # my_tree_lp123.heading("Artikelnummer", text="PartNo", anchor=W)
    # my_tree_lp123.heading("Benämning", text="Description", anchor=W)
    # my_tree_lp123.heading("Restkvantitet", text="Quantity", anchor=W)
    # my_tree_lp123.heading("Batch/Serienr", text="Batch or SN", anchor=W)
    # my_tree_lp123.heading("PL_ID", text="PartLocationId", anchor=W)
    # my_tree_lp123.heading("PR_ID", text="ProductRecordId", anchor=W)
    # my_tree_lp123.heading("PART_ID", text="ProductRecordId", anchor=W)
    # my_tree_lp123.heading("GS1_CODE", text="GS1_CODE", anchor=W)
    # my_tree_lp123.heading("Lagerplats", text="Lagerplats", anchor=W)
    # my_tree_lp123.heading("EF_VALUE", text="EF_VALUE", anchor=W)
    #
    # my_tree_lp123.grid(row=4, column=1, padx=(0, 2), sticky=W)
    #
    #
    #
    #
    # canvas3 = Canvas(dev_plan, width=200, height=80, background='white')
    # canvas3.grid(row=0, column=1, rowspan=3, columnspan=3, sticky=W, padx=1, pady=10)
    #
    # canvas_lp_1 = Canvas(tab2, width=900, height=80, background='white')
    # canvas_lp_1.grid(row=0, column=1, rowspan=3, columnspan=3, sticky=W, padx=10, pady=10)

    # Style för TreeView
    style = ttk.Style()
    style.configure("TButton", padding=10, relief="flat", background="white", foreground="black", anchor="center")
    # style.theme_use("clam")
    style.configure(".", font=('Helvetica', 12), foreground="black")
    style.configure("Treeview", foreground='black', rowheight=25)
    style.configure("Treeview.Heading", foreground='black', font=('Helvetica', 12, "bold"))

    # Skal till TreeView för att hämta information från om lagerplats
    # tree_frame = Frame(tab2)
    # tree_frame.grid(row=4, column=1, ipady=80, ipadx=180, padx=10, sticky=W)
    # tree_scroll = ttk.Scrollbar(tree_frame)
    # tree_scroll.pack(side=RIGHT, fill=Y)
    # my_tree_lp = ttk.Treeview(tree_frame, style="Custom.Treeview", yscrollcommand=tree_scroll.set, columns=("Artikelnummer", "Benämning", "Restkvantitet", "Batch/Serienr", "PL_ID", "PR_ID", "PART_ID", "GS1_CODE", "EF_VALUE"), displaycolumns=("Artikelnummer", "Benämning", "Restkvantitet", "Batch/Serienr"))
    # tree_scroll.config(command=my_tree_lp.yview)
    # # my_tree_lp['columns'] = ("Artikelnummer", "Benämning", "Restkvantitet", "Batchnummer", "Serienummer", "Test")
    # my_tree_lp.column("#0", anchor=W, width=1, minwidth=1, stretch=0)
    # my_tree_lp.column("Artikelnummer", anchor=W, width=80)
    # my_tree_lp.column("Benämning", anchor=W, width=150)
    # my_tree_lp.column("Restkvantitet", anchor=W, width=80)
    # my_tree_lp.column("Batch/Serienr", anchor=W, width=60)
    # my_tree_lp.column("PL_ID", anchor=W, width=60)
    # my_tree_lp.column("PR_ID", anchor=W, width=60)
    # my_tree_lp.column("PART_ID", anchor=W, width=60)
    # my_tree_lp.column("GS1_CODE", anchor=W, width=60)
    # my_tree_lp.column("EF_VALUE", anchor=W, width=60)
    #
    # my_tree_lp.heading("#0", text="", anchor=W)
    # my_tree_lp.heading("Artikelnummer", text="PartNo", anchor=W)
    # my_tree_lp.heading("Benämning", text="Description", anchor=W)
    # my_tree_lp.heading("Restkvantitet", text="Quantity", anchor=W)
    # my_tree_lp.heading("Batch/Serienr", text="Batch or SN", anchor=W)
    # my_tree_lp.heading("PL_ID", text="PartLocationId", anchor=W)
    # my_tree_lp.heading("PR_ID", text="ProductRecordId", anchor=W)
    # my_tree_lp.heading("PART_ID", text="ProductRecordId", anchor=W)
    # my_tree_lp.heading("GS1_CODE", text="GS1_CODE", anchor=W)
    # my_tree_lp.heading("EF_VALUE", text="EF_VALUE", anchor=W)
    # my_tree_lp.pack(fill='both', expand=True)
    # my_tree_lp.grid(row=4, column=1, ipady=80, ipadx=180, padx=10, sticky=W)

    # # Skal till TreeView för att hämta information från plocklista
    # tree_frame_plock1 = Frame(tab1)
    # tree_frame_plock1.grid(row=4, column=1, ipady=5, padx=4, sticky=W)
    # tree_scroll_plock1 = ttk.Scrollbar(tree_frame_plock1)
    # tree_scroll_plock1.pack(side=RIGHT, fill=Y)
    # my_tree = ttk.Treeview(tree_frame_plock1, style="Custom.Treeview", yscrollcommand=tree_scroll_plock1.set)
    # my_tree.tag_configure("Test", background="lightgrey", font=('Helvetica', 12, "italic"))
    # my_tree.tag_configure("Test1", background="white")
    # tree_scroll_plock1.config(command=my_tree.yview)
    # my_tree['columns'] = ("Artikelnummer", "Benämning", "Restkvantitet", "Lagerplats", "Spårbarhet")
    # my_tree['displaycolumns'] = ("Artikelnummer", "Benämning", "Restkvantitet", "Lagerplats")
    # my_tree.column("#0", width=1, minwidth=1, stretch=0)
    # my_tree.column("Artikelnummer", anchor=W, width=140)
    # my_tree.column("Benämning", anchor=W, width=220)
    # my_tree.column("Restkvantitet", anchor=W, width=70)
    # my_tree.column("Lagerplats", anchor=W, width=90)
    # my_tree.column("Spårbarhet", anchor=W, width=70)
    #
    # my_tree.heading("#0", text="", anchor=W)
    # my_tree.heading("Artikelnummer", text="PartNo", anchor=W)
    # my_tree.heading("Benämning", text="Description", anchor=W)
    # my_tree.heading("Restkvantitet", text="RestQ", anchor=W)
    # my_tree.heading("Lagerplats", text="Location", anchor=W)
    # my_tree.heading("Spårbarhet", text="Trac.", anchor=W)
    # my_tree.pack(fill='both', expand=True)
    # # my_tree.grid(row=4, column=1, ipady=5, padx=4, sticky=W)
    #
    # # Skal till TreeView för att hämta information om redan plockad kvantitet
    # tree_frame_plock2 = Frame(tab1)
    # tree_frame_plock2.grid(row=5, column=1, ipady=5, padx=4, sticky=W)
    # tree_scroll_plock2 = ttk.Scrollbar(tree_frame_plock2)
    # tree_scroll_plock2.pack(side=RIGHT, fill=Y)
    # my_tree1 = ttk.Treeview(tree_frame_plock2, style="Custom.Treeview",yscrollcommand=tree_scroll_plock2.set)
    # tree_scroll_plock2.config(command=my_tree1.yview)
    # # my_tree1 = ttk.Treeview(tab1)
    # my_tree1['columns'] = ("Artikelnummer", "Benämning", "Plockad kvantitet", "Lagerplats", "Spårbarhet")
    # my_tree1['displaycolumns'] = ("Artikelnummer", "Benämning", "Plockad kvantitet", "Lagerplats")
    # my_tree1.column("#0", width=1, minwidth=1, stretch=0)
    # my_tree1.column("Artikelnummer", anchor=W, width=140)
    # my_tree1.column("Benämning", anchor=W, width=220)
    # my_tree1.column("Plockad kvantitet", anchor=W, width=70)
    # my_tree1.column("Lagerplats", anchor=W, width=90)
    # my_tree1.column("Spårbarhet", anchor=W, width=70)
    #
    # my_tree1.heading("#0", text="", anchor=W)
    # my_tree1.heading("Artikelnummer", text="PartNo", anchor=W)
    # my_tree1.heading("Benämning", text="Description", anchor=W)
    # my_tree1.heading("Plockad kvantitet", text="PickedQ", anchor=W)
    # my_tree1.heading("Lagerplats", text="Location", anchor=W)
    # my_tree1.heading("Spårbarhet", text="Trac.", anchor=W)
    # my_tree1.pack(fill='both', expand=True)
    # # my_tree1.grid(row=5, column=1, ipady=5, padx=4, sticky=W)

    # Skal till TreeView delivery planning
    # my_tree_dev_plan = ttk.Treeview(dev_plan, style="Custom.Treeview",)
    # my_tree_dev_plan['columns'] = ("Nr", "Namn", "Datum", "Vikt", "Volym", "Artiklar", "Rader", "Person", "Status")
    # my_tree_dev_plan.column("#0", width=1, minwidth=1)
    # my_tree_dev_plan.column("Nr", anchor=W, width=40)
    # my_tree_dev_plan.column("Namn", anchor=W, width=165)
    # my_tree_dev_plan.column("Datum", anchor=W, width=120)
    # my_tree_dev_plan.column("Vikt", anchor=W, width=60)
    # my_tree_dev_plan.column("Volym", anchor=W, width=80)
    # my_tree_dev_plan.column("Artiklar", anchor=W, width=60)
    # my_tree_dev_plan.column("Rader", anchor=W, width=60)
    # my_tree_dev_plan.column("Person", anchor=W, width=80)
    # my_tree_dev_plan.column("Status", anchor=W, width=70)
    #
    # my_tree_dev_plan.heading("#0", text="", anchor=W)
    # my_tree_dev_plan.heading("Nr", text="PL", anchor=W)
    # my_tree_dev_plan.heading("Namn", text="Cu. Name", anchor=W)
    # my_tree_dev_plan.heading("Datum", text="Date", anchor=W)
    # my_tree_dev_plan.heading("Vikt", text="Weight", anchor=W)
    # my_tree_dev_plan.heading("Volym", text="Volume", anchor=W)
    # my_tree_dev_plan.heading("Artiklar", text="Parts", anchor=W)
    # my_tree_dev_plan.heading("Rader", text="Rows", anchor=W)
    # my_tree_dev_plan.heading("Person", text="Picker", anchor=W)
    # my_tree_dev_plan.heading("Status", text="Status", anchor=W)
    # my_tree_dev_plan.grid(row=5, column=1, ipady=3, padx=10, sticky=W, columnspan=3)

    # tree_frame_plock2 = Frame(tab1)
    # tree_frame_plock2.grid(row=5, column=1, ipady=5, padx=4, sticky=W)
    # tree_scroll_plock2 = Scrollbar(tree_frame_plock2)
    # tree_scroll_plock2.pack(side=RIGHT, fill=Y)
    # my_tree1 = ttk.Treeview(tree_frame_plock2, yscrollcommand=tree_scroll_plock2.set)
    # tree_scroll_plock2.config(command=my_tree1.yview)

    # my_tree_lagerplats_frame = Frame(tab4)
    # my_tree_lagerplats_frame.grid(row=10, column=1, ipady=3, padx=10, sticky=W, columnspan=3)
    # tree_scroll_lagerplats = ttk.Scrollbar(my_tree_lagerplats_frame)
    # tree_scroll_lagerplats.pack(side=RIGHT, fill=Y)
    # my_tree_lagerplats = ttk.Treeview(my_tree_lagerplats_frame, style="Custom.Treeview",yscrollcommand=tree_scroll_lagerplats.set)  # , columns=("Lagerinfo", "Saldo"), displaycolumns=("Lagerinfo", "Saldo"))
    # tree_scroll_lagerplats.config(command=my_tree_lagerplats.yview)
    # Skal till TreeView lagerplats
    # my_tree_lagerplats = ttk.Treeview(tab4)
    # my_tree_lagerplats['columns'] = ("Lagerinfo", "Saldo")
    # my_tree_lagerplats.column("#0", width=1, minwidth=1, stretch=0)
    # my_tree_lagerplats.column("Lagerinfo", anchor=W, width=200)
    # my_tree_lagerplats.column("Saldo", anchor=W, width=180)
    # # my_tree_lagerplats.column("Datum", anchor=W, width=100)
    # # my_tree_lagerplats.column("Vikt", anchor=W, width=50)
    # # my_tree_lagerplats.column("Volym", anchor=W, width=80)
    # # my_tree_lagerplats.column("Artiklar", anchor=W, width=80)
    # # my_tree_lagerplats.column("Rader", anchor=W, width=60)
    # # my_tree_lagerplats.column("Person", anchor=W, width=80)
    # # my_tree_lagerplats.column("Status", anchor=W, width=65)
    #
    # my_tree_lagerplats.heading("#0", text="", anchor=W)
    # my_tree_lagerplats.heading("Lagerinfo", text="Stock info", anchor=W)
    # my_tree_lagerplats.heading("Saldo", text="Quantity", anchor=W)
    # # my_tree_lagerplats.heading("Datum", text="Datum", anchor=W)
    # # my_tree_lagerplats.heading("Vikt", text="Vikt", anchor=W)
    # # my_tree_lagerplats.heading("Volym", text="Volym", anchor=W)
    # # my_tree_lagerplats.heading("Artiklar", text="Artiklar", anchor=W)
    # # my_tree_lagerplats.heading("Rader", text="Rader", anchor=W)
    # # my_tree_lagerplats.heading("Person", text="Plockare", anchor=W)
    # # my_tree_lagerplats.heading("Status", text="Status", anchor=W)
    # # my_tree_lagerplats.grid(row=10, column=1, ipady=3, padx=10, sticky=W, columnspan=3)
    #
    #
    #
    # # Entry till torder
    #
    # # Label till info
    # Label_torder_info = Label(tab4, text=f"                                                                                                                                 \n"
    #                                      f"                                                                                                                                 ", font=("Calibri", 14), bg="White")
    # Label_torder_info.grid(row=8, column=1, pady=20, padx=10, columnspan=1, sticky=S)
    #
    # # Label till info
    # Label_torder_info1 = Label(tab4, text=f"                           ", font=("Calibri", 20), bg="White")
    # Label_torder_info1.grid(row=9, column=1, pady=20, padx=10, columnspan=1, sticky=W + E)

    window.mainloop()
