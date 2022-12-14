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
from tkinter import ttk
import requests
import urllib3
from ttkthemes import ThemedTk
from dateutil.relativedelta import *
from multiprocessing import Queue

# Om vi har trial period!
trialperiod = '2023-01-31 07:00:00'
now = str(datetime.now())
if now > trialperiod:
    window1 = ThemedTk(theme="blue")
    window1.geometry("930x750")
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

    #ODBC = parser['ODBC']['DSN']

    #lagerplats_otvattat
    lagerplats_otvattat = parser['logics']['lagerplats_otvattat']
    lagerplats = parser['logics']['lagerplats']
    lagerstalle = parser['logics']['lagerstalle']
    leverantorskod_uthyrning = parser['logics']['leverantorskod_uthyrning']
    LS_huvud = parser['logics']['LS_huvud']
    LS_uthyrning = parser['logics']['LS_uthyrning']
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
    inleverans_ef_sn.append(serienummer_utrangeratpris)
    inleverans_ef_sn.append(serienummer_utrangeratdatum)


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
    window.geometry("930x750")
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
            pass
            #messagebox.showerror("Error", f"Issues with selecting the record {e}")


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
            combobox_IL.set("")
            combobox_IL_2.set("")
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
                    tom_lista = []
                    update_function_IL(tom_lista)
                    update_function_IL_lenght(tom_lista)
                    IL_entry_ordernumber.delete(0, END)
                    IL_entry_ordernumber.focus_set()
                    messagebox.showerror("Error", f'Not able to fetch the purchase order')
                else:
                    part_numbers = []
                    length_list = []
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
                            lenght_lenght = str(i["RowsGoodsLabel"])
                            part_numbers.append(partnumber)
                            length_list.append(lenght_lenght)
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
                    part_numbers.sort()
                    part_numbers = list(set(part_numbers))
                    length_list.sort()
                    length_list = list(set(length_list))
                    update_function_IL(part_numbers)
                    update_function_IL_lenght(length_list)

        except Exception as e:
            tom_lista = []
            update_function_IL(tom_lista)
            update_function_IL_lenght(tom_lista)
            IL_entry_ordernumber.delete(0, END)
            IL_entry_ordernumber.focus_set()
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

                WH_url = f"https://{host}/sv/{company}/api/v1/Common/Warehouses?$filter=Code eq '{LS_huvud}'"

                def RetryWH(s, max_tries=40):
                    counter = 0
                    while True:
                        reportResulst = s.get(url=WH_url, verify=False)
                        if reportResulst.status_code == 200:
                            return reportResulst

                        counter += 1
                        if counter == max_tries:
                            messagebox.showinfo("Error", f'Not able to fetch the connected customerorder row')
                            break

                        if reportResulst.status_code != 200:
                            r = Retry1(s)
                        time.sleep(0.4)

                WH_Get = RetryWH(s)
                WH_Get_json = WH_Get.json()
                wh_id = int(WH_Get_json[0]["Id"])

                pl_id_url = f"https://{host}/sv/{company}/api/v1/Inventory/PartLocations?$filter=PartId eq {int(t)} and WarehouseId eq {int(wh_id)} and Name eq '{lagerplats}' and LifeCycleState eq 10&$TOP=1"

                def RetryPL_ID(s, max_tries=40):
                    counter = 0
                    while True:
                        reportResulst = s.get(url=pl_id_url, verify=False)
                        if reportResulst.status_code == 200:
                            return reportResulst

                        counter += 1
                        if counter == max_tries:
                            messagebox.showinfo("Error", f'Not able to fetch the connected customerorder row')
                            break

                        if reportResulst.status_code != 200:
                            r = Retry1(s)
                        time.sleep(0.4)

                pl_id_get = RetryPL_ID(s)


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
                json = None

                if pl_id_get.text == [] or pl_id_get.text == "[]":
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
                elif pl_id_get.text != [] or pl_id_get.text != "[]":
                    pl_id_get_json = pl_id_get.json()
                    json = {
                        "PurchaseOrderRowId": int(r),
                        "Quantity": float(o),
                        "DeleteFutureRest": False,
                        "Locations": [{
                            "PartLocationId": int(pl_id_get_json[0]["Id"]),
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
                                          "ChargeNumber": {"Value": str(q)}
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
        combobox_IL.set("")
        combobox_IL_2.set("")
        tom = []
        combobox_IL.config(postcommand=get_new_values_ComboBox_IL(tom))
        combobox_IL_2.config(postcommand=get_new_values_ComboBox_IL(tom))
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

    options_IL_ComboBox = ['']
    selected_IL_ComboBox = StringVar(tab1)
    selected_IL_ComboBox.set("")
    combobox_IL = ttk.Combobox(tab1, values=options_IL_ComboBox, state="normal", textvariable=selected_IL_ComboBox)

    options_IL_ComboBox_2 = ['']
    selected_IL_ComboBox_2 = StringVar(tab1)
    selected_IL_ComboBox_2.set("")
    combobox_IL_2 = ttk.Combobox(tab1, values=options_IL_ComboBox_2, state="normal", textvariable=selected_IL_ComboBox_2)

    def backend_get_new_values_ComboBox_IL(listar):
        listar = listar
        # Gör saker som uppdaterar ComboBox
        return listar

    def get_new_values_ComboBox_IL(recieve_list_1):
        recieve_list_1.append("")
        recieve_list_1.sort()
        listar = backend_get_new_values_ComboBox_IL(recieve_list_1)
        combobox_IL["values"] = listar
        #combobox_IL_2["values"] = listar

    def update_function_IL(recieve_list):
        combobox_IL.config(postcommand=get_new_values_ComboBox_IL(recieve_list))
        #combobox_IL_2.config(postcommand=get_new_values_ComboBox_IL(recieve_list))

    def backend_get_new_values_ComboBox_IL_lenght(listar):
        listar = listar
        # Gör saker som uppdaterar ComboBox
        return listar

    def get_new_values_ComboBox_IL_lenght(recieve_list_1):
        recieve_list_1.append("")
        recieve_list_1.sort()
        listar = backend_get_new_values_ComboBox_IL(recieve_list_1)
        #combobox_IL["values"] = listar
        combobox_IL_2["values"] = listar

    def update_function_IL_lenght(recieve_list):
        #combobox_IL.config(postcommand=get_new_values_ComboBox_IL(recieve_list))
        combobox_IL_2.config(postcommand=get_new_values_ComboBox_IL_lenght(recieve_list))

    def populate_treeview_recieve_with_combo(events):
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
                    # part_numbers = []
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
                            # part_numbers.append(partnumber)
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
                            if str(combobox_IL.get()) == "" and str(combobox_IL_2.get()) == "":
                                my_tree.insert('', 'end', values=(partnumber, desc, restquantity, recieveQ, unit_code, length, id, part_id, price))
                            elif str(combobox_IL.get()) != "" and str(combobox_IL_2.get()) == "":
                                if str(combobox_IL.get()) == str(partnumber):
                                    my_tree.insert('', 'end', values=(partnumber, desc, restquantity, recieveQ, unit_code, length, id, part_id, price))
                                else:
                                    pass
                            elif str(combobox_IL.get()) == "" and str(combobox_IL_2.get()) != "":
                                if str(combobox_IL_2.get()) == str(length):
                                    my_tree.insert('', 'end', values=(partnumber, desc, restquantity, recieveQ, unit_code, length, id, part_id, price))
                                else:
                                    pass
                            elif str(combobox_IL_2.get()) != "" and str(combobox_IL.get()) != "":
                                if str(combobox_IL.get()) == str(partnumber) and str(combobox_IL_2.get()) == str(length):
                                    my_tree.insert('', 'end', values=(partnumber, desc, restquantity, recieveQ, unit_code, length, id, part_id, price))
                                else:
                                    pass

                    # part_numbers.sort()
                    # part_numbers = list(set(part_numbers))
                    # update_function_IL(part_numbers)

        except Exception as e:
            messagebox.showerror("Error", f"Issues with populating the treeview {e}")


    combobox_IL.grid(row=3, column=0, padx=(10, 0), pady=1, sticky=W, ipadx=10)
    combobox_IL_2.grid(row=3, column=3, padx=(30, 0), pady=1, sticky=E, ipadx=10)

    combobox_IL.bind("<<ComboboxSelected>>", populate_treeview_recieve_with_combo)
    combobox_IL_2.bind("<<ComboboxSelected>>", populate_treeview_recieve_with_combo)

    def populate_treeview_dispatch(events):
        try:
            for u in my_tree_ul.get_children():
                my_tree_ul.delete(u)
            combobox_UL.set("")
            combobox_UL_2.set("")
            # BAJSKORV
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
                    tom_lista = []
                    update_function_UL(tom_lista)
                    update_function_UL_lenght(tom_lista)
                    UL_entry_ordernumber.delete(0, END)
                    UL_entry_ordernumber.focus_set()
                    messagebox.showerror("Error", f'Not able to fetch the customer order')
                else:

                    partnumbers = []
                    length_list = []
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
                                    partnumbers.append(str(partnumber))
                                    length_list.append(str(length))
                                    serial_numbers_w_length = f"https://{host}/sv/{company}/api/v1/Inventory/ProductRecords?$filter=PartId eq {int(part_id)} and ChargeNumber eq '{length}'"

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
                    partnumbers.sort()
                    partnumbers = list(set(partnumbers))
                    length_list.sort()
                    length_list = list(set(length_list))
                    update_function_UL(partnumbers)
                    update_function_UL_lenght(length_list)

        except Exception as e:
            tom_lista = []
            update_function_UL(tom_lista)
            update_function_UL_lenght(tom_lista)
            UL_entry_ordernumber.delete(0, END)
            UL_entry_ordernumber.focus_set()
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
                    serial_numbers_w_length = f"https://{host}/sv/{company}/api/v1/Inventory/ProductRecords?$filter=PartId eq {int(partid)} and ChargeNumber eq '{langd}'&$orderby=ActualArrivalDate desc"

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

                                        #################################################################################
                                        WH_url = f"https://{host}/sv/{company}/api/v1/Common/Warehouses?$filter=Code eq '{LS_uthyrning}'"

                                        def RetryWH(s, max_tries=40):
                                            counter = 0
                                            while True:
                                                reportResulst = s.get(url=WH_url, verify=False)
                                                if reportResulst.status_code == 200:
                                                    return reportResulst

                                                counter += 1
                                                if counter == max_tries:
                                                    messagebox.showinfo("Error", f'Not able to fetch the connected customerorder row')
                                                    break

                                                if reportResulst.status_code != 200:
                                                    r = Retry1(s)
                                                time.sleep(0.4)

                                        WH_Get = RetryWH(s)
                                        WH_Get_json = WH_Get.json()
                                        wh_id = int(WH_Get_json[0]["Id"])

                                        pl_id_url = f"https://{host}/sv/{company}/api/v1/Inventory/PartLocations?$filter=PartId eq {int(partid)} and WarehouseId eq {int(wh_id)} and Name eq '{stock_location}' and LifeCycleState eq 10&$TOP=1"

                                        def RetryPL_ID(s, max_tries=40):
                                            counter = 0
                                            while True:
                                                reportResulst = s.get(url=pl_id_url, verify=False)
                                                if reportResulst.status_code == 200:
                                                    return reportResulst

                                                counter += 1
                                                if counter == max_tries:
                                                    messagebox.showinfo("Error", f'Not able to fetch the connected customerorder row')
                                                    break

                                                if reportResulst.status_code != 200:
                                                    r = Retry1(s)
                                                time.sleep(0.4)

                                        pl_id_get = RetryPL_ID(s)

                                        json_1 = None

                                        if pl_id_get.text == [] or pl_id_get.text == "[]":
                                            json_1 = {
                                                "PurchaseOrderRowId": int(ioren["Id"]),
                                                "Quantity": float(len(co_and_rows_json["ProductRecordIds"])),
                                                "DeleteFutureRest": False,
                                                "Locations": [{
                                                    "PartLocationName": f"{stock_location}",
                                                    "Quantity": float(len(co_and_rows_json["ProductRecordIds"]))  # ,
                                                    # "ProductRecords": serials_do_keys
                                                }]
                                            }
                                        elif pl_id_get.text != [] or pl_id_get.text != "[]":
                                            pl_id_get_json = pl_id_get.json()
                                            json_1 = {
                                                "PurchaseOrderRowId": int(ioren["Id"]),
                                                "Quantity": float(len(co_and_rows_json["ProductRecordIds"])),
                                                "DeleteFutureRest": False,
                                                "Locations": [{
                                                    "PartLocationId": int(pl_id_get_json[0]["Id"]),
                                                    "Quantity": float(len(co_and_rows_json["ProductRecordIds"]))  # ,
                                                    # "ProductRecords": serials_do_keys
                                                }]
                                            }
                                        #################################################################################

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
        tom_lista = []
        update_function_UL(tom_lista)
        update_function_UL_lenght(tom_lista)
        for u in my_tree_ul.get_children():
            my_tree_ul.delete(u)
        UL_entry_ordernumber.delete(0, END)
        UL_entry_recieve.delete(0, END)
        UL_entry_ordernumber.focus_set()

        # Uppdatera extra fälten på serienummer härnäst
    # Entry till ordernummer
    UL_entry_ordernumber = ttk.Entry(tab2, font=("Calibri", 14))
    UL_entry_ordernumber.grid(row=2, column=0, padx=(10, 0), pady=(0, 40), sticky=W)
    UL_entry_ordernumber.bind("<Return>", populate_treeview_dispatch)

    options_UL_ComboBox = ['']
    selected_UL_ComboBox = StringVar(tab2)
    selected_UL_ComboBox.set("")
    combobox_UL = ttk.Combobox(tab2, values=options_UL_ComboBox, state="normal", textvariable=selected_UL_ComboBox)

    options_UL_ComboBox_2 = ['']
    selected_UL_ComboBox_2 = StringVar(tab2)
    selected_UL_ComboBox_2.set("")
    combobox_UL_2 = ttk.Combobox(tab2, values=options_UL_ComboBox_2, state="normal", textvariable=selected_UL_ComboBox_2)


    def backend_get_new_values_ComboBox_UL(listar):
        listar = listar
        # Gör saker som uppdaterar ComboBox
        return listar


    def get_new_values_ComboBox_UL(recieve_list_1):
        recieve_list_1.append("")
        recieve_list_1.sort()
        listar = backend_get_new_values_ComboBox_UL(recieve_list_1)
        combobox_UL["values"] = listar
        # combobox_IL_2["values"] = listar


    def update_function_UL(recieve_list):
        combobox_UL.config(postcommand=get_new_values_ComboBox_UL(recieve_list))
        # combobox_IL_2.config(postcommand=get_new_values_ComboBox_IL(recieve_list))


    def backend_get_new_values_ComboBox_UL_lenght(listar):
        listar = listar
        # Gör saker som uppdaterar ComboBox
        return listar


    def get_new_values_ComboBox_UL_lenght(recieve_list_1):
        recieve_list_1.append("")
        recieve_list_1.sort()
        listar = backend_get_new_values_ComboBox_UL(recieve_list_1)
        # combobox_IL["values"] = listar
        combobox_UL_2["values"] = listar


    def update_function_UL_lenght(recieve_list):
        # combobox_IL.config(postcommand=get_new_values_ComboBox_IL(recieve_list))
        combobox_UL_2.config(postcommand=get_new_values_ComboBox_UL_lenght(recieve_list))


    def populate_treeview_UL_with_combo(events):
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

                    partnumbers = []
                    length_list = []
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
                                    partnumbers.append(str(partnumber))
                                    length_list.append(str(length))
                                    serial_numbers_w_length = f"https://{host}/sv/{company}/api/v1/Inventory/ProductRecords?$filter=PartId eq {int(part_id)} and ChargeNumber eq '{length}'"

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
                                        if str(combobox_UL.get()) == "" and str(combobox_UL_2.get()) == "":
                                            my_tree_ul.insert('', 'end', values=(partnumber, desc, restquantity, recieveQ, unit_code, length, id, part_id))
                                        elif str(combobox_UL.get()) != "" and str(combobox_UL_2.get()) == "":
                                            if str(combobox_UL.get()) == str(partnumber):
                                                my_tree_ul.insert('', 'end', values=(partnumber, desc, restquantity, recieveQ, unit_code, length, id, part_id))
                                            else:
                                                pass
                                        elif str(combobox_UL.get()) == "" and str(combobox_UL_2.get()) != "":
                                            if str(combobox_UL_2.get()) == str(length):
                                                my_tree_ul.insert('', 'end', values=(partnumber, desc, restquantity, recieveQ, unit_code, length, id, part_id))
                                            else:
                                                pass
                                        elif str(combobox_UL_2.get()) != "" and str(combobox_UL.get()) != "":
                                            if str(combobox_UL.get()) == str(partnumber) and str(combobox_UL_2.get()) == str(length):
                                                my_tree_ul.insert('', 'end', values=(partnumber, desc, restquantity, recieveQ, unit_code, length, id, part_id))
                                            else:
                                                pass

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
                                        if str(combobox_UL.get()) == "" and str(combobox_UL_2.get()) == "":
                                            my_tree_ul.insert('', 'end', values=(partnumber, desc, restquantity, recieveQ, unit_code, length, id, part_id))
                                        elif str(combobox_UL.get()) != "" and str(combobox_UL_2.get()) == "":
                                            if str(combobox_UL.get()) == str(partnumber):
                                                my_tree_ul.insert('', 'end', values=(partnumber, desc, restquantity, recieveQ, unit_code, length, id, part_id))
                                            else:
                                                pass
                                        elif str(combobox_UL.get()) == "" and str(combobox_UL_2.get()) != "":
                                            if str(combobox_UL_2.get()) == str(length):
                                                my_tree_ul.insert('', 'end', values=(partnumber, desc, restquantity, recieveQ, unit_code, length, id, part_id))
                                            else:
                                                pass
                                        elif str(combobox_UL_2.get()) != "" and str(combobox_UL.get()) != "":
                                            if str(combobox_UL.get()) == str(partnumber) and str(combobox_UL_2.get()) == str(length):
                                                my_tree_ul.insert('', 'end', values=(partnumber, desc, restquantity, recieveQ, unit_code, length, id, part_id))
                                            else:
                                                pass

                                except Exception as e:
                                    for u in my_tree_ul.get_children():
                                        my_tree_ul.delete(u)
                                    messagebox.showerror("Error", f"Issues with converting the length on at least one row")
                                    UL_entry_ordernumber.delete(0, END)
                                    UL_entry_ordernumber.focus_set()
                    partnumbers.sort()
                    partnumbers = list(set(partnumbers))
                    length_list.sort()
                    length_list = list(set(length_list))
                    update_function_UL(partnumbers)
                    update_function_UL_lenght(length_list)

        except Exception as e:
            messagebox.showerror("Error", f"Issues with populating the treeview {e}")


    combobox_UL.grid(row=2, column=0, padx=(10, 0), pady=(40, 0), sticky=W, ipadx=10)
    combobox_UL_2.grid(row=2, column=3, padx=(30, 0), pady=(40, 0), sticky=E, ipadx=10)

    combobox_UL.bind("<<ComboboxSelected>>", populate_treeview_UL_with_combo)
    combobox_UL_2.bind("<<ComboboxSelected>>", populate_treeview_UL_with_combo)
    #HÄRHÄR
    # Skal till TreeView för att hämta information från plocklista
    tree_frame_plock1 = Frame(tab1)
    tree_frame_plock1.grid(row=4, column=0, sticky=W, columnspan=4, ipady=70, pady=(0, 10), padx=(10, 0))
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
    IL_label_recieve.grid(row=5, column=0, padx=(10, 0), pady=(0, 0), sticky=W)
    IL_entry_recieve = ttk.Entry(tab1, font=("Calibri", 14))
    IL_entry_recieve.grid(row=6, column=0, padx=(10, 0), pady=(0, 50), sticky=W)

    IL_label_length = ttk.Label(tab1, text="Längd: ", font=("Calibri", 14, "bold"))
    IL_label_length.grid(row=5, column=1, padx=(2, 0), pady=(0, 0), sticky=W)
    IL_entry_length = ttk.Entry(tab1, font=("Calibri", 14))
    IL_entry_length.grid(row=6, column=1, padx=(2, 0), pady=(0, 50), sticky=W)



    IL_button_edit = ttk.Button(tab1, text="Uppdatera", style="my.TButton", command=update_record_IL)
    IL_button_edit.grid(row=5, column=2, padx=(2, 0), pady=(0, 5), ipadx=30, sticky=W)
    IL_button_recieve = ttk.Button(tab1, text="Inleverera", style="my.TButton", command=report_recieve)
    IL_button_recieve.grid(row=5, column=3, padx=(2, 0), pady=(0, 5), ipadx=30, sticky=W)



    my_tree.bind('<ButtonRelease-1>', select_record_IL)

    #canvas_lp_11 = Canvas(tab5, width=900, height=80, background='white')
    #canvas_lp_11.grid(row=0, column=1, rowspan=3, columnspan=3, sticky=W, padx=10, pady=10)




    # tab2: Design Utleverans

    # Funktion för att populera treeview utleverans



    UL_label_rutin = ttk.Label(tab2, text="Utleverera lagerorder", font=("Calibri", 18, "bold"))
    UL_label_rutin.grid(row=0, column=0, padx=(10, 0), pady=(2, 20), sticky=W, columnspan=2)

    # Label till ordernummer i rapportera inleverans
    UL_label_ordernumber = ttk.Label(tab2, text="Ordernummer: ", font=("Calibri", 14, "bold"))
    UL_label_ordernumber.grid(row=1, column=0, padx=(10, 0), pady=1, sticky=W)



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
            #tab3.config(cursor="watch")
            #tab3.update()
            for u in my_tree_AL.get_children():
                my_tree_AL.delete(u)
            combobox_AL.set("")
            combobox_AL_2.set("")
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
                    customer_url = f"https://{host}/sv/{company}/api/v1/Sales/Customers?$filter=Code eq '{ordernumber}'"

                    def RetryCustomer(s, max_tries=40):
                        counter = 0
                        while True:
                            reportResulst = s.get(url=customer_url, verify=False)
                            if reportResulst.status_code == 200:
                                return reportResulst

                            counter += 1
                            if counter == max_tries:
                                messagebox.showerror("Error", f'Not able to fetch the warehouse')
                                break

                            if reportResulst.status_code != 200:
                                r = Retry1(s)
                            time.sleep(0.4)

                    customer_get = RetryCustomer(s)
                    customer_get_json = customer_get.json()
                    if customer_get_json == []:
                        tom_lista = []
                        update_function_AL(tom_lista)
                        update_function_AL_lenght(tom_lista)
                        AL_entry_ordernumber.delete(0, END)
                        AL_entry_ordernumber.focus_set()
                        combobox_AL.set("")
                        combobox_AL_2.set("")
                        AL_label_customer["text"] = ""
                        AL_label_mark["text"] = "Antal markerade rader: "
                        messagebox.showerror("Error", f'Not able to fetch the customer information')
                    else:
                        part_numbers = []
                        lengths = []
                        kundnamn = customer_get_json[0]["Name"]
                        AL_label_customer["text"] = kundnamn

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
                                        part_numbers.append(str(part_get_json[0]["PartNumber"]))
                                        lengths.append(str(pr_get_json[0]["ChargeNumber"]))

                                        my_tree_AL.insert('', 'end', values=(0, pr_get_json[0]["SerialNumber"], part_get_json[0]["PartNumber"], part_get_json[0]["Description"], pr_get_json[0]["ChargeNumber"], pr_get_json[0]["ChargeNumber"], 1, part_id, iora['ProductRecordId'], iora["Quantity"], iora["PartLocationId"]))
                        part_numbers.sort()
                        partnumbers = list(set(part_numbers))
                        lengths.sort()
                        length_list = list(set(lengths))
                        update_function_AL(partnumbers)
                        update_function_AL_lenght(length_list)
            #tab3.config(cursor="")

        except Exception as e:
            #(cursor="")
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
            AL_label_mark["text"] = f"Antal markerade rader: {len(my_tree_AL.selection())}"
        except Exception as e:
            messagebox.showerror("Error", f"Issues with selecting the record {e}")
    #TEST

    # Funktion för att uppdatera rad i rapportera utleveransrutinen
    def update_record_AL():
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
            #AL_mark_as_return
        except Exception as e:
            messagebox.showerror("Error", f"Issues with updating the record {e}")

        # Funktion för att ankomstrapportera


    def create_invoice():
        try:
            #tab3.config(cursor="watch")
            #tab3.update()
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

                customer_id = f"https://{host}/sv/{company}/api/v1/Sales/Customers?$filter=Code eq '{AL_entry_ordernumber.get()}'"

                def RetryCust(s, max_tries=40):
                    counter = 0
                    while True:
                        reportResulst = s.get(url=customer_id, verify=False)
                        if reportResulst.status_code == 200:
                            return reportResulst

                        counter += 1
                        if counter == max_tries:
                            messagebox.showerror("Error", f'Not able to fetch the pricelist for the customer')
                            break

                        if reportResulst.status_code != 200:
                            r = Retry1(s)
                        time.sleep(0.4)

                cust_price = RetryCust(s)
                cust_price_json = cust_price.json()
                pricelist_id = int(cust_price_json[0]["PriceListId"])
                end_customer_id = int(cust_price_json[0]["Id"])

                WH_url = f"https://{host}/sv/{company}/api/v1/Common/Warehouses?$filter=Code eq '{LS_huvud}'"

                def RetryWH(s, max_tries=40):
                    counter = 0
                    while True:
                        reportResulst = s.get(url=WH_url, verify=False)
                        if reportResulst.status_code == 200:
                            return reportResulst

                        counter += 1
                        if counter == max_tries:
                            messagebox.showinfo("Error", f'Not able to fetch the connected customerorder row')
                            break

                        if reportResulst.status_code != 200:
                            r = Retry1(s)
                        time.sleep(0.4)

                WH_Get = RetryWH(s)
                WH_Get_json = WH_Get.json()
                wh_id_real = int(WH_Get_json[0]["Id"])

                customer_order_rows = []
                for var_aterlamna, var_serienummer, var_artnr, var_ben, var_uthyrd, var_ater, var_rengor, var_partid, var_pr_id, var_quantity, var_pl_id in zip(aterlamna, serienummer, artnr, ben, uthyrd, ater, rengor, partid, pr_id, quantity, pl_id):
                    if var_aterlamna == 1:

                        price_real = f"https://{host}/sv/{company}/api/v1/Sales/SalesPrices?$filter=PriceListId eq {pricelist_id} and PartId eq {int(var_partid)}"

                        def RetryPrice(s, max_tries=40):
                            counter = 0
                            while True:
                                reportResulst = s.get(url=price_real, verify=False)
                                if reportResulst.status_code == 200:
                                    return reportResulst

                                counter += 1
                                if counter == max_tries:
                                    messagebox.showerror("Error", f'Not able to fetch the pricelist for the customer')
                                    break

                                if reportResulst.status_code != 200:
                                    r = Retry1(s)
                                time.sleep(0.4)

                        real_price = RetryPrice(s)
                        real_price_json = real_price.json()
                        real_price_price = float(real_price_json[0]["FuturePrice"])

                        #TODO: först hämta extra fält på ursprungligt serienummer, kan lika gärna göra det jämt

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
                                if ef_result.text == [] or ef_result.text == "[]":
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
                                if ef_result.text == [] or ef_result.text == "[]":
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
                                if ef_result.text == [] or ef_result.text == "[]":
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
                                if ef_result.text == [] or ef_result.text == "[]":
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
                                if ef_result.text == [] or ef_result.text == "[]":
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
                                if ef_result.text == [] or ef_result.text == "[]":
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
                                if ef_result.text == [] or ef_result.text == "[]":
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
                                if ef_result.text == [] or ef_result.text == "[]":
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
                                if ef_result.text == [] or ef_result.text == "[]":
                                    pass
                                else:
                                    ef_result_json = ef_result.json()
                                    SERUTRANGD = (ef_result_json[0]["DateOnlyValue"])
                                    SERUTRANGD = str(SERUTRANGD[0:10])

                        #TODO: sedan skapa nytt serienummer om det diffar i längd


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
                        nextserial = int(next_serial_number_string[3:])
                        nextserial_final = nextserial+1


                        create_PO = f"https://{host}/sv/{company}/api/v1/Purchase/PurchaseOrders/Create"
                        json_create_po = {
                                              "SupplierId": int(supplier_code),
                                              "OrderTypeId": int(purchase_ordertype_id),
                                              "IsStockOrder": True
                                            }

                        def RetryCPO(s, max_tries=40):
                            counter = 0
                            while True:
                                reportResulst = s.post(url=create_PO, json=json_create_po, verify=False)
                                if reportResulst.status_code == 200:
                                    return reportResulst

                                counter += 1
                                if counter == max_tries:
                                    messagebox.showerror("Error", f'Couldnt create the purchase order')
                                    break

                                if reportResulst.status_code != 200:
                                    r = Retry1(s)
                                time.sleep(0.4)

                        create_po_create = RetryCPO(s)
                        create_po_create_json = create_po_create.json()
                        po_id = create_po_create_json["EntityId"]


                        create_PO_row = f"https://{host}/sv/{company}/api/v1/Purchase/PurchaseOrders/AddRow"
                        json_create_po_row = {
                                                  "PurchaseOrderId": int(po_id),
                                                  "PartId": int(var_partid),
                                                  "OrderedQuantity": 1.0,
                                                  "OrderRowType": int(1)
                                                }

                        def RetryCPOR(s, max_tries=40):
                            counter = 0
                            while True:
                                reportResulst = s.post(url=create_PO_row, json=json_create_po_row, verify=False)
                                if reportResulst.status_code == 200:
                                    return reportResulst

                                counter += 1
                                if counter == max_tries:
                                    messagebox.showerror("Error", f'Couldnt create the row on the purchase order')
                                    break

                                if reportResulst.status_code != 200:
                                    r = Retry1(s)
                                time.sleep(0.4)

                        create_po_row_create = RetryCPOR(s)
                        create_po_row_create_json = create_po_row_create.json()
                        por_id = create_po_row_create_json["EntityId"]



                        linked_cust_order = f"https://{host}/sv/{company}/api/v1/Purchase/PurchaseOrderRows?$filter=Id eq {int(por_id)}"

                        def RetryLINKED(s, max_tries=40):
                            counter = 0
                            while True:
                                reportResulst = s.get(url=linked_cust_order, verify=False)
                                if reportResulst.status_code == 200:
                                    return reportResulst

                                counter += 1
                                if counter == max_tries:
                                    messagebox.showinfo("Error", f'Not able to fetch the connected customerorder row')
                                    break

                                if reportResulst.status_code != 200:
                                    r = Retry1(s)
                                time.sleep(0.4)

                        linked_cust_order_get = RetryLINKED(s)
                        linked_cust_order_get_json = linked_cust_order_get.json()
                        linked_stock_order_id = int(linked_cust_order_get_json[0]["LinkedStockOrderRowId"])

                        json_del = {
                                      "Rows": [
                                          {
                                              "CustomerOrderRowId": linked_stock_order_id,
                                              "Quantity": 1.0,
                                              "DeleteFutureRest": False,
                                              "Locations": [
                                                  {
                                                      "Quantity": 1.0,
                                                      "PartLocationId": int(var_pl_id),
                                                      "ProductRecordId": int(var_pr_id)
                                                  }
                                              ]
                                          }
                                      ]
    }
                        url_post_deli = f"https://{host}/sv/{company}/api/v1/Sales/CustomerOrders/ReportDeliveries"

                        def RetryDA(s, max_tries=40):
                            counter = 0
                            while True:
                                reportResulst = s.post(url=url_post_deli, json=json_del, verify=False)
                                if reportResulst.status_code == 200:
                                    return reportResulst

                                counter += 1
                                if counter == max_tries:
                                    messagebox.showerror("Error", f'Not able to report arrival on a row on the purchase order, status message: {reportResulst.text}')
                                    break

                                if reportResulst.status_code != 200:
                                    r = Retry1(s)
                                time.sleep(0.4)

                        del_and_rows = RetryDA(s)
                        del_and_rows_json = del_and_rows.json()

                        ######################################################################
                        WH_url = f"https://{host}/sv/{company}/api/v1/Common/Warehouses?$filter=Code eq '{LS_huvud}'"

                        def RetryWH(s, max_tries=40):
                            counter = 0
                            while True:
                                reportResulst = s.get(url=WH_url, verify=False)
                                if reportResulst.status_code == 200:
                                    return reportResulst

                                counter += 1
                                if counter == max_tries:
                                    messagebox.showinfo("Error", f'Not able to fetch the connected customerorder row')
                                    break

                                if reportResulst.status_code != 200:
                                    r = Retry1(s)
                                time.sleep(0.4)

                        WH_Get = RetryWH(s)
                        WH_Get_json = WH_Get.json()
                        wh_id = int(WH_Get_json[0]["Id"])

                        pl_id_url = f"https://{host}/sv/{company}/api/v1/Inventory/PartLocations?$filter=PartId eq {int(var_partid)} and WarehouseId eq {int(wh_id)} and Name eq '{lagerplats_otvattat}' and LifeCycleState eq 10&$TOP=1"

                        def RetryPL_ID(s, max_tries=40):
                            counter = 0
                            while True:
                                reportResulst = s.get(url=pl_id_url, verify=False)
                                if reportResulst.status_code == 200:
                                    return reportResulst

                                counter += 1
                                if counter == max_tries:
                                    messagebox.showinfo("Error", f'Not able to fetch the connected customerorder row')
                                    break

                                if reportResulst.status_code != 200:
                                    r = Retry1(s)
                                time.sleep(0.4)

                        pl_id_get = RetryPL_ID(s)

                        json = None

                        if pl_id_get.text == [] or pl_id_get.text == "[]":
                            json = {
                                "PurchaseOrderRowId": int(por_id),
                                "Quantity": float(1.0),
                                "DeleteFutureRest": False,
                                "Locations": [{
                                    "PartLocationName": f"{lagerplats_otvattat}",
                                    "Quantity": float(1.0)
                                }]
                            }
                        elif pl_id_get.text != [] or pl_id_get.text != "[]":
                            pl_id_get_json = pl_id_get.json()
                            json = {
                                "PurchaseOrderRowId": int(por_id),
                                "Quantity": float(1.0),
                                "DeleteFutureRest": False,
                                "Locations": [{
                                    "PartLocationId": int(pl_id_get_json[0]["Id"]),
                                    "Quantity": float(1.0)
                                }]
                            }
                        ######################################################################


                        url_post_arrivals = f"https://{host}/sv/{company}/api/v1/Purchase/PurchaseOrders/ReportArrivals"
                        json = {
                            "Rows": [json]
                        }

                        def RetryRA(s, max_tries=40):
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

                        po_and_rows = RetryRA(s)
                        po_and_rows_json = po_and_rows.json()
                        product_old_record_id = po_and_rows_json["ProductRecordIds"][0]



                        if var_uthyrd != var_ater and (var_ater != "0" or var_ater != 0):
                            WH_url = f"https://{host}/sv/{company}/api/v1/Common/Warehouses?$filter=Code eq '{LS_huvud}'"

                            def RetryWH(s, max_tries=40):
                                counter = 0
                                while True:
                                    reportResulst = s.get(url=WH_url, verify=False)
                                    if reportResulst.status_code == 200:
                                        return reportResulst

                                    counter += 1
                                    if counter == max_tries:
                                        messagebox.showinfo("Error", f'Not able to fetch the connected customerorder row')
                                        break

                                    if reportResulst.status_code != 200:
                                        r = Retry1(s)
                                    time.sleep(0.4)

                            WH_Get = RetryWH(s)
                            WH_Get_json = WH_Get.json()
                            wh_id = int(WH_Get_json[0]["Id"])

                            pl_id_url = f"https://{host}/sv/{company}/api/v1/Inventory/PartLocations?$filter=PartId eq {int(var_partid)} and WarehouseId eq {int(wh_id)} and Name eq '{lagerplats_otvattat}' and LifeCycleState eq 10&$TOP=1"

                            def RetryPL_ID(s, max_tries=40):
                                counter = 0
                                while True:
                                    reportResulst = s.get(url=pl_id_url, verify=False)
                                    if reportResulst.status_code == 200:
                                        return reportResulst

                                    counter += 1
                                    if counter == max_tries:
                                        messagebox.showinfo("Error", f'Not able to fetch the connected customerorder row')
                                        break

                                    if reportResulst.status_code != 200:
                                        r = Retry1(s)
                                    time.sleep(0.4)

                            invent_pr_json = None
                            pl_id_get = RetryPL_ID(s)
                            invent_pr = f"https://{host}/sv/{company}/api/v1/Inventory/Parts/ReportStockCount"
                            if pl_id_get.text == [] or pl_id_get.text == "[]":
                                invent_pr_json = {
                                    "PartId": int(var_partid),
                                    "WarehouseId": int(wh_id),
                                    "Name": f"{lagerplats_otvattat}",
                                    "Balance": 1.0,
                                    "SerialNumber": "SER" + f"{nextserial_final}"
                                }
                            elif pl_id_get.text != [] or pl_id_get.text != "[]":
                                pl_id_json = pl_id_get.json()
                                pl_id = int(pl_id_json[0]["Id"])
                                invent_pr_json = {
                                    "PartId": int(var_partid),
                                    "WarehouseId": int(wh_id),
                                    "PartLocationId": int(pl_id),
                                    "Balance": (float(1.0)),
                                    "SerialNumber": "SER" + f"{nextserial_final}"
                                }




                            def RetryInvent(s, max_tries=40):
                                counter = 0
                                while True:
                                    reportResulst = s.post(url=invent_pr, json=invent_pr_json, verify=False)
                                    if reportResulst.status_code == 200:
                                        return reportResulst

                                    counter += 1
                                    if counter == max_tries:
                                        messagebox.showerror("Error", f'Not able to update the charge numbers, since the row has been reported arrival, \nplease update the charge numbers manually')
                                        break

                                    if reportResulst.status_code != 200:
                                        r = Retry1(s)
                                    time.sleep(0.4)

                            invent_update = RetryInvent(s)
                            invent_update_json = invent_update.json()

                            pr_pr = f"https://{host}/sv/{company}/api/v1/Inventory/ProductRecords?$filter=SerialNumber eq 'SER{nextserial_final}'"

                            def RetryPRPR(s, max_tries=40):
                                counter = 0
                                while True:
                                    reportResulst = s.get(url=pr_pr, verify=False)
                                    if reportResulst.status_code == 200:
                                        return reportResulst

                                    counter += 1
                                    if counter == max_tries:
                                        messagebox.showinfo("Error", f'Not able to find the starting product record')
                                        break

                                    if reportResulst.status_code != 200:
                                        r = Retry1(s)
                                    time.sleep(0.4)

                            pr_pr_get = RetryPRPR(s)
                            pr_pr_get_json = pr_pr_get.json()
                            product_new_record_id = int(pr_pr_get_json[0]["Id"])

                            pr_pl = f"https://{host}/sv/{company}/api/v1/Inventory/PartLocationProductRecords?$filter=ProductRecordId eq {int(product_new_record_id)} and Quantity Gt 0"

                            def RetryPRPL(s, max_tries=40):
                                counter = 0
                                while True:
                                    reportResulst = s.get(url=pr_pl, verify=False)
                                    if reportResulst.status_code == 200:
                                        return reportResulst

                                    counter += 1
                                    if counter == max_tries:
                                        messagebox.showinfo("Error", f'Did not find the part location for the product record')
                                        break

                                    if reportResulst.status_code != 200:
                                        r = Retry1(s)
                                    time.sleep(0.4)

                            pr_pl_get = RetryPRPL(s)
                            pr_pl_get_json = pr_pl_get.json()
                            pr_new_pl_id = int(pr_pl_get_json[0]["PartLocationId"])

                            url_product_record_update = f"https://{host}/sv/{company}/api/v1/Inventory/ProductRecords/SetProperties"
                            json_product_record = {
                                "ProductRecordId": int(product_new_record_id),
                                "ChargeNumber": {"Value": str(int(var_uthyrd)-int(var_ater))}
                            }

                            def RetryZZ(s, max_tries=40):
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

                            product_record_update = RetryZZ(s)
                            product_record_update_json = product_record_update.json()

                            # serienummer_tillgangskonto = parser['logics_EF']['serienummer_tillgangskonto']
                            # serienummer_avskrivningskonto = parser['logics_EF']['serienummer_avskrivningskonto']
                            # serienummer_anskaffningsvarde = parser['logics_EF']['serienummer_anskaffningsvarde']
                            # serienummer_restvarde = parser['logics_EF']['serienummer_restvarde']
                            # serienummer_avskriven = parser['logics_EF']['serienummer_avskriven']
                            # serienummer_avskrivningstid = parser['logics_EF']['serienummer_avskrivningstid']
                            # serienummer_klar = parser['logics_EF']['serienummer_klar']
                            # serienummer_utrangeratpris = parser['logics_EF']['serienummer_utrangeratpris']
                            # serienummer_utrangeratdatum = parser['logics_EF']['serienummer_utrangeratdatum']
                            anskaffningsvarde_ny = round(float(SERANSKA)*float((int(var_uthyrd)-int(var_ater))/int(var_uthyrd)), 2)
                            anskaffningsvarde_gammal = round(float(SERANSKA)*float(1-((int(var_uthyrd)-int(var_ater))/int(var_uthyrd))), 2)
                            restvarde_ny = round(float(SERRESTV)*float((int(var_uthyrd)-int(var_ater))/int(var_uthyrd)), 2)
                            restvarde_gammal = round(float(SERRESTV)*float(1-((int(var_uthyrd)-int(var_ater))/int(var_uthyrd))), 2)


                            lista_ef_ny_pr = []
                            for j in inleverans_ef_sn:
                                date_now = datetime.now().date()
                                if j == serienummer_utrangeratpris:
                                    lista_ef_ny_pr.append({"Identifier": serienummer_utrangeratpris, "DecimalValue": float(float((int(var_uthyrd)-int(var_ater))/1000)*float(real_price_price))})
                                elif j == serienummer_utrangeratdatum:
                                    lista_ef_ny_pr.append({"Identifier": serienummer_utrangeratdatum, "DateOnlyValue": f"{date_now}"})
                                elif j == serienummer_anskaffningsvarde:
                                    lista_ef_ny_pr.append({"Identifier": serienummer_anskaffningsvarde, "DecimalValue": float(anskaffningsvarde_ny)})
                                elif j == serienummer_restvarde:
                                    lista_ef_ny_pr.append({"Identifier": serienummer_restvarde, "DecimalValue": float(restvarde_ny)})
                                elif j == serienummer_avskrivningskonto:
                                    lista_ef_ny_pr.append({"Identifier": serienummer_avskrivningskonto, "IntegerValue": int(SERAVSKR)})
                                elif j == serienummer_klar:
                                    lista_ef_ny_pr.append({"Identifier": serienummer_klar, "DateOnlyValue": f"{str(SERKLAR)}"})
                                elif j == serienummer_avskrivningstid:
                                    lista_ef_ny_pr.append({"Identifier": serienummer_avskrivningstid, "IntegerValue": int(SERAVSTID)})
                                elif j == serienummer_tillgangskonto:
                                    lista_ef_ny_pr.append({"Identifier": serienummer_tillgangskonto, "IntegerValue": int(SERTILLG)})

                            url_ef_value_sn = f"https://{host}/sv/{company}/api/v1/Common/Commands/SetExtraFieldValues"
                            json_ef_values = {
                                "EntityId": int(product_new_record_id),
                                "EntityType": 0,
                                "Values": lista_ef_ny_pr
                            }

                            def Retry7(s, max_tries=40):
                                counter = 0
                                while True:
                                    reportResulst = s.post(url=url_ef_value_sn, json=json_ef_values, verify=False)
                                    if reportResulst.status_code == 200:
                                        return reportResulst

                                    counter += 1
                                    if counter == max_tries:
                                        messagebox.showerror("Error", f'Was not able to set extra field values on product record id {product_new_record_id}')
                                        break

                                    if reportResulst.status_code != 200:
                                        r = Retry1(s)
                                    time.sleep(0.4)

                            ef_values_update = Retry7(s)
                            ef_values_update_json = ef_values_update.json()
                            #KUKENSTÅR

                            url_product_record_update_old = f"https://{host}/sv/{company}/api/v1/Inventory/ProductRecords/SetProperties"
                            json_product_record_old = {
                                "ProductRecordId": int(product_old_record_id),
                                "ChargeNumber": {"Value": str(int(var_uthyrd)-(int(var_uthyrd) - int(var_ater)))}
                            }

                            def Retry_old_pr(s, max_tries=40):
                                counter = 0
                                while True:
                                    reportResulst = s.post(url=url_product_record_update_old, json=json_product_record_old, verify=False)
                                    if reportResulst.status_code == 200:
                                        return reportResulst

                                    counter += 1
                                    if counter == max_tries:
                                        messagebox.showerror("Error", f'Not able to update the charge numbers, since the row has been reported arrival, \nplease update the charge numbers manually')
                                        break

                                    if reportResulst.status_code != 200:
                                        r = Retry1(s)
                                    time.sleep(0.4)

                            product_record_update_old = Retry_old_pr(s)
                            product_record_update_old_json = product_record_update_old.json()

                            lista_ef_gammal_pr = []
                            for j in inleverans_ef_sn:
                                date_now = datetime.now().date()

                                if j == serienummer_anskaffningsvarde:
                                    lista_ef_gammal_pr.append({"Identifier": serienummer_anskaffningsvarde, "DecimalValue": float(anskaffningsvarde_gammal)})
                                elif j == serienummer_restvarde:
                                    lista_ef_gammal_pr.append({"Identifier": serienummer_restvarde, "DecimalValue": float(restvarde_gammal)})

                            url_ef_value_sn_old = f"https://{host}/sv/{company}/api/v1/Common/Commands/SetExtraFieldValues"
                            json_ef_values_old = {
                                "EntityId": int(product_old_record_id),
                                "EntityType": 0,
                                "Values": lista_ef_gammal_pr
                            }

                            def Retryold(s, max_tries=40):
                                counter = 0
                                while True:
                                    reportResulst = s.post(url=url_ef_value_sn_old, json=json_ef_values_old, verify=False)
                                    if reportResulst.status_code == 200:
                                        return reportResulst

                                    counter += 1
                                    if counter == max_tries:
                                        messagebox.showerror("Error", f'Was not able to set extra field values on product record id {product_new_record_id}')
                                        break

                                    if reportResulst.status_code != 200:
                                        r = Retry1(s)
                                    time.sleep(0.4)

                            ef_values_update_old = Retryold(s)
                            ef_values_update_old_json = ef_values_update_old.json()

                            if var_rengor == 1 or var_rengor == "1":
                                part_rengor = None

                                for ef_value in artikel_ef:
                                    if ef_value == f'{artikel_rengoring}':
                                        ef_url = f"https://{host}/sv/{company}/api/v1/Common/ExtraFields?$filter=ParentId eq {int(var_partid)} and Identifier eq '{ef_value}'"

                                        def RetryEFEF(s, max_tries=40):
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

                                        ef_result = RetryEFEF(s)
                                        if ef_result.text == [] or ef_result.text == "[]":
                                            pass
                                        else:
                                            ef_result_json = ef_result.json()
                                            part_rengor = str(ef_result_json[0]["StringValue"])
                                if part_rengor != None:
                                    rengor_part = f"https://{host}/sv/{company}/api/v1/Inventory/Parts?$filter=PartNumber eq '{str(part_rengor)}'"

                                    def RetryRENGOR(s, max_tries=40):
                                        counter = 0
                                        while True:
                                            reportResulst = s.get(url=rengor_part, verify=False)
                                            if reportResulst.status_code == 200:
                                                return reportResulst

                                            counter += 1
                                            if counter == max_tries:
                                                messagebox.showinfo("Error1", f'Did not find the part id for the cleaning part')
                                                break

                                            if reportResulst.status_code != 200:
                                                r = Retry1(s)
                                            time.sleep(0.4)

                                    rengor_get = RetryRENGOR(s)
                                    rengor_get_json = rengor_get.json()
                                    rengor_id = int(rengor_get_json[0]["Id"])
                                    rengor_unit_id = int(rengor_get_json[0]["StandardUnitId"])

                                    post_price_info = f"https://{host}/sv/{company}/api/v1/Sales/CustomerOrders/GetPriceInfo"
                                    json_post_price_info = {
                                        "PartId": int(rengor_id),
                                          "CustomerId": int(end_customer_id),
                                          "UnitId": int(rengor_unit_id),
                                          "QuantityInUnit": 1.0,
                                          "UseExtendedResult": True
                                    }

                                    def RetryPRICE(s, max_tries=40):
                                        counter = 0
                                        while True:
                                            reportResulst = s.post(url=post_price_info, json=json_post_price_info, verify=False)
                                            if reportResulst.status_code == 200:
                                                return reportResulst

                                            counter += 1
                                            if counter == max_tries:
                                                messagebox.showerror("Error", f'Couldnt fetch the price for the cleaning part')
                                                break

                                            if reportResulst.status_code != 200:
                                                r = Retry1(s)
                                            time.sleep(0.4)

                                    post_price_info_get = RetryPRICE(s)
                                    if post_price_info_get.text == [] or post_price_info_get.text == "[]":
                                        rengor_price_final = float(0)
                                    else:
                                        post_price_info_get_json = post_price_info_get.json()
                                        rengor_price_final = float(post_price_info_get_json["UnitPrice"])
                                    if rengor_price_final != 0:
                                        customer_order_rows.append({
                                            "PartId": int(rengor_id),
                                            "OrderedQuantity": 1.0,
                                            "Price": round(float(float((int(var_uthyrd) - int(var_ater)) / 1000) * float(rengor_price_final)), 2),
                                            "WarehouseId": int(wh_id),
                                            "OrderRowType": 1,
                                            "AffectStockBalance": False
                                        })



                                customer_order_rows.append({
                                    "PartId": int(var_partid),
                                    "OrderedQuantity": 1.0,
                                    "Price": round(float(float((int(var_uthyrd) - int(var_ater)) / 1000) * float(real_price_price)), 2),
                                    "WarehouseId": int(wh_id),
                                    "OrderRowType": 1,
                                    "AffectStockBalance": True,
                                    "DeliveryReportingLocations": [
                                        {
                                            "Quantity": 1.0,
                                            "PartLocationId": int(pr_new_pl_id),
                                            "ProductRecordId": int(product_new_record_id)
                                        }
                                    ]
                                })

                            else:
                                customer_order_rows.append({
                                                "PartId": int(var_partid),
                                                "OrderedQuantity": 1.0,
                                                "Price": round(float(float((int(var_uthyrd)-int(var_ater))/1000)*float(real_price_price)), 2),
                                                "WarehouseId": int(wh_id),
                                                "OrderRowType": 1,
                                                "AffectStockBalance": True,
                                                "DeliveryReportingLocations": [
                                                                                {
                                                                            "Quantity": 1.0,
                                                                            "PartLocationId": int(pr_new_pl_id),
                                                                            "ProductRecordId": int(product_new_record_id)
                                                                                }
                                            ]
                                            })
                        elif var_ater == "0" or var_ater == 0:
                            WH_url = f"https://{host}/sv/{company}/api/v1/Common/Warehouses?$filter=Code eq '{LS_huvud}'"

                            def RetryWH(s, max_tries=40):
                                counter = 0
                                while True:
                                    reportResulst = s.get(url=WH_url, verify=False)
                                    if reportResulst.status_code == 200:
                                        return reportResulst

                                    counter += 1
                                    if counter == max_tries:
                                        messagebox.showinfo("Error", f'Not able to fetch the connected customerorder row')
                                        break

                                    if reportResulst.status_code != 200:
                                        r = Retry1(s)
                                    time.sleep(0.4)

                            WH_Get = RetryWH(s)
                            WH_Get_json = WH_Get.json()
                            wh_id = int(WH_Get_json[0]["Id"])

                            # invent_pr = f"https://{host}/sv/{company}/api/v1/Inventory/Parts/ReportStockCount"
                            # invent_pr_json = {
                            #     "PartId": int(var_partid),
                            #     "WarehouseId": int(wh_id),
                            #     "Name": f"{lagerplats_otvattat}",
                            #     "Balance": 1.0,
                            #     "SerialNumber": "SER" + f"{nextserial_final}"
                            # }
                            #
                            # def RetryInvent(s, max_tries=40):
                            #     counter = 0
                            #     while True:
                            #         reportResulst = s.post(url=invent_pr, json=invent_pr_json, verify=False)
                            #         if reportResulst.status_code == 200:
                            #             return reportResulst
                            #
                            #         counter += 1
                            #         if counter == max_tries:
                            #             messagebox.showerror("Error", f'Not able to update the charge numbers, since the row has been reported arrival, \nplease update the charge numbers manually')
                            #             break
                            #
                            #         if reportResulst.status_code != 200:
                            #             r = Retry1(s)
                            #         time.sleep(0.4)
                            #
                            # invent_update = RetryInvent(s)
                            # invent_update_json = invent_update.json()
                            #
                            pr_pr = f"https://{host}/sv/{company}/api/v1/Inventory/ProductRecords?$filter=Id eq {int(var_pr_id)}"

                            def RetryPRPR(s, max_tries=40):
                                counter = 0
                                while True:
                                    reportResulst = s.get(url=pr_pr, verify=False)
                                    if reportResulst.status_code == 200:
                                        return reportResulst

                                    counter += 1
                                    if counter == max_tries:
                                        messagebox.showinfo("Error", f'Not able to find the starting product record')
                                        break

                                    if reportResulst.status_code != 200:
                                        r = Retry1(s)
                                    time.sleep(0.4)

                            pr_pr_get = RetryPRPR(s)
                            pr_pr_get_json = pr_pr_get.json()
                            product_old_old_record_id = int(pr_pr_get_json[0]["Id"])
                            #
                            pr_pl = f"https://{host}/sv/{company}/api/v1/Inventory/PartLocationProductRecords?$filter=ProductRecordId eq {int(product_old_old_record_id)} and Quantity Gt 0"

                            def RetryPRPL(s, max_tries=40):
                                counter = 0
                                while True:
                                    reportResulst = s.get(url=pr_pl, verify=False)
                                    if reportResulst.status_code == 200:
                                        return reportResulst

                                    counter += 1
                                    if counter == max_tries:
                                        messagebox.showinfo("Error", f'Did not find the part location for the product record')
                                        break

                                    if reportResulst.status_code != 200:
                                        r = Retry1(s)
                                    time.sleep(0.4)

                            pr_pl_get = RetryPRPL(s)
                            pr_pl_get_json = pr_pl_get.json()
                            pr_old_pl_id = int(pr_pl_get_json[0]["PartLocationId"])
                            #
                            # url_product_record_update = f"https://{host}/sv/{company}/api/v1/Inventory/ProductRecords/SetProperties"
                            # json_product_record = {
                            #     "ProductRecordId": int(product_new_record_id),
                            #     "ChargeNumber": {"Value": str(int(var_uthyrd) - int(var_ater))}
                            # }
                            #
                            # def RetryZZ(s, max_tries=40):
                            #     counter = 0
                            #     while True:
                            #         reportResulst = s.post(url=url_product_record_update, json=json_product_record, verify=False)
                            #         if reportResulst.status_code == 200:
                            #             return reportResulst
                            #
                            #         counter += 1
                            #         if counter == max_tries:
                            #             messagebox.showerror("Error", f'Not able to update the charge numbers, since the row has been reported arrival, \nplease update the charge numbers manually')
                            #             break
                            #
                            #         if reportResulst.status_code != 200:
                            #             r = Retry1(s)
                            #         time.sleep(0.4)
                            #
                            # product_record_update = RetryZZ(s)
                            # product_record_update_json = product_record_update.json()

                            # serienummer_tillgangskonto = parser['logics_EF']['serienummer_tillgangskonto']
                            # serienummer_avskrivningskonto = parser['logics_EF']['serienummer_avskrivningskonto']
                            # serienummer_anskaffningsvarde = parser['logics_EF']['serienummer_anskaffningsvarde']
                            # serienummer_restvarde = parser['logics_EF']['serienummer_restvarde']
                            # serienummer_avskriven = parser['logics_EF']['serienummer_avskriven']
                            # serienummer_avskrivningstid = parser['logics_EF']['serienummer_avskrivningstid']
                            # serienummer_klar = parser['logics_EF']['serienummer_klar']
                            # serienummer_utrangeratpris = parser['logics_EF']['serienummer_utrangeratpris']
                            # serienummer_utrangeratdatum = parser['logics_EF']['serienummer_utrangeratdatum']
                            # anskaffningsvarde_ny = round(float(SERANSKA) * float((int(var_uthyrd) - int(var_ater)) / int(var_uthyrd)), 2)
                            # anskaffningsvarde_gammal = round(float(SERANSKA) * float(1 - ((int(var_uthyrd) - int(var_ater)) / int(var_uthyrd))), 2)
                            # restvarde_ny = round(float(SERRESTV) * float((int(var_uthyrd) - int(var_ater)) / int(var_uthyrd)), 2)
                            # restvarde_gammal = round(float(SERRESTV) * float(1 - ((int(var_uthyrd) - int(var_ater)) / int(var_uthyrd))), 2)
                            #
                            # lista_ef_ny_pr = []
                            # for j in inleverans_ef_sn:
                            #     date_now = datetime.now().date()
                            #     if j == serienummer_utrangeratpris:
                            #         lista_ef_ny_pr.append({"Identifier": serienummer_utrangeratpris, "DecimalValue": float(float((int(var_uthyrd) - int(var_ater)) / 1000) * float(real_price_price))})
                            #     elif j == serienummer_utrangeratdatum:
                            #         lista_ef_ny_pr.append({"Identifier": serienummer_utrangeratdatum, "DateOnlyValue": f"{date_now}"})
                            #     elif j == serienummer_anskaffningsvarde:
                            #         lista_ef_ny_pr.append({"Identifier": serienummer_anskaffningsvarde, "DecimalValue": float(anskaffningsvarde_ny)})
                            #     elif j == serienummer_restvarde:
                            #         lista_ef_ny_pr.append({"Identifier": serienummer_restvarde, "DecimalValue": float(restvarde_ny)})
                            #     elif j == serienummer_avskrivningskonto:
                            #         lista_ef_ny_pr.append({"Identifier": serienummer_avskrivningskonto, "IntegerValue": int(SERAVSKR)})
                            #     elif j == serienummer_klar:
                            #         lista_ef_ny_pr.append({"Identifier": serienummer_klar, "DateOnlyValue": f"{str(SERKLAR)}"})
                            #     elif j == serienummer_avskrivningstid:
                            #         lista_ef_ny_pr.append({"Identifier": serienummer_avskrivningstid, "IntegerValue": int(SERAVSTID)})
                            #     elif j == serienummer_tillgangskonto:
                            #         lista_ef_ny_pr.append({"Identifier": serienummer_tillgangskonto, "IntegerValue": int(SERTILLG)})

                            # url_ef_value_sn = f"https://{host}/sv/{company}/api/v1/Common/Commands/SetExtraFieldValues"
                            # json_ef_values = {
                            #     "EntityId": int(product_new_record_id),
                            #     "EntityType": 0,
                            #     "Values": lista_ef_ny_pr
                            # }
                            #
                            # def Retry7(s, max_tries=40):
                            #     counter = 0
                            #     while True:
                            #         reportResulst = s.post(url=url_ef_value_sn, json=json_ef_values, verify=False)
                            #         if reportResulst.status_code == 200:
                            #             return reportResulst
                            #
                            #         counter += 1
                            #         if counter == max_tries:
                            #             messagebox.showerror("Error", f'Was not able to set extra field values on product record id {product_new_record_id}')
                            #             break
                            #
                            #         if reportResulst.status_code != 200:
                            #             r = Retry1(s)
                            #         time.sleep(0.4)
                            #
                            # ef_values_update = Retry7(s)
                            # ef_values_update_json = ef_values_update.json()

                            # url_product_record_update_old = f"https://{host}/sv/{company}/api/v1/Inventory/ProductRecords/SetProperties"
                            # json_product_record_old = {
                            #     "ProductRecordId": int(product_old_record_id),
                            #     "ChargeNumber": {"Value": str(int(var_uthyrd) - (int(var_uthyrd) - int(var_ater)))}
                            # }
                            #
                            # def Retry_old_pr(s, max_tries=40):
                            #     counter = 0
                            #     while True:
                            #         reportResulst = s.post(url=url_product_record_update_old, json=json_product_record_old, verify=False)
                            #         if reportResulst.status_code == 200:
                            #             return reportResulst
                            #
                            #         counter += 1
                            #         if counter == max_tries:
                            #             messagebox.showerror("Error", f'Not able to update the charge numbers, since the row has been reported arrival, \nplease update the charge numbers manually')
                            #             break
                            #
                            #         if reportResulst.status_code != 200:
                            #             r = Retry1(s)
                            #         time.sleep(0.4)
                            #
                            # product_record_update_old = Retry_old_pr(s)
                            # product_record_update_old_json = product_record_update_old.json()
                            #
                            # lista_ef_gammal_pr = []
                            # for j in inleverans_ef_sn:
                            #     date_now = datetime.now().date()
                            #
                            #     if j == serienummer_anskaffningsvarde:
                            #         lista_ef_gammal_pr.append({"Identifier": serienummer_anskaffningsvarde, "DecimalValue": float(anskaffningsvarde_gammal)})
                            #     elif j == serienummer_restvarde:
                            #         lista_ef_gammal_pr.append({"Identifier": serienummer_restvarde, "DecimalValue": float(restvarde_gammal)})
                            #
                            # url_ef_value_sn_old = f"https://{host}/sv/{company}/api/v1/Common/Commands/SetExtraFieldValues"
                            # json_ef_values_old = {
                            #     "EntityId": int(product_old_record_id),
                            #     "EntityType": 0,
                            #     "Values": lista_ef_gammal_pr
                            # }
                            #
                            # def Retryold(s, max_tries=40):
                            #     counter = 0
                            #     while True:
                            #         reportResulst = s.post(url=url_ef_value_sn_old, json=json_ef_values_old, verify=False)
                            #         if reportResulst.status_code == 200:
                            #             return reportResulst
                            #
                            #         counter += 1
                            #         if counter == max_tries:
                            #             messagebox.showerror("Error", f'Was not able to set extra field values on product record id {product_new_record_id}')
                            #             break
                            #
                            #         if reportResulst.status_code != 200:
                            #             r = Retry1(s)
                            #         time.sleep(0.4)
                            #
                            # ef_values_update_old = Retryold(s)
                            # ef_values_update_old_json = ef_values_update_old.json()

                            if var_rengor == 1 or var_rengor == "1":
                                part_rengor = None

                                for ef_value in artikel_ef:
                                    if ef_value == f'{artikel_rengoring}':
                                        ef_url = f"https://{host}/sv/{company}/api/v1/Common/ExtraFields?$filter=ParentId eq {int(var_partid)} and Identifier eq '{ef_value}'"

                                        def RetryEFEF(s, max_tries=40):
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

                                        ef_result = RetryEFEF(s)
                                        if ef_result.text == [] or ef_result.text == "[]":
                                            pass
                                        else:
                                            ef_result_json = ef_result.json()
                                            part_rengor = str(ef_result_json[0]["StringValue"])
                                if part_rengor != None:
                                    rengor_part = f"https://{host}/sv/{company}/api/v1/Inventory/Parts?$filter=PartNumber eq '{str(part_rengor)}'"

                                    def RetryRENGOR(s, max_tries=40):
                                        counter = 0
                                        while True:
                                            reportResulst = s.get(url=rengor_part, verify=False)
                                            if reportResulst.status_code == 200:
                                                return reportResulst

                                            counter += 1
                                            if counter == max_tries:
                                                messagebox.showinfo("Error1", f'Did not find the part id for the cleaning part')
                                                break

                                            if reportResulst.status_code != 200:
                                                r = Retry1(s)
                                            time.sleep(0.4)

                                    rengor_get = RetryRENGOR(s)
                                    rengor_get_json = rengor_get.json()
                                    rengor_id = int(rengor_get_json[0]["Id"])
                                    rengor_unit_id = int(rengor_get_json[0]["StandardUnitId"])

                                    post_price_info = f"https://{host}/sv/{company}/api/v1/Sales/CustomerOrders/GetPriceInfo"
                                    json_post_price_info = {
                                        "PartId": int(rengor_id),
                                        "CustomerId": int(end_customer_id),
                                        "UnitId": int(rengor_unit_id),
                                        "QuantityInUnit": 1.0,
                                        "UseExtendedResult": True
                                    }

                                    def RetryPRICE(s, max_tries=40):
                                        counter = 0
                                        while True:
                                            reportResulst = s.post(url=post_price_info, json=json_post_price_info, verify=False)
                                            if reportResulst.status_code == 200:
                                                return reportResulst

                                            counter += 1
                                            if counter == max_tries:
                                                messagebox.showerror("Error", f'Couldnt fetch the price for the cleaning part')
                                                break

                                            if reportResulst.status_code != 200:
                                                r = Retry1(s)
                                            time.sleep(0.4)

                                    post_price_info_get = RetryPRICE(s)
                                    if post_price_info_get.text == [] or post_price_info_get.text == "[]":
                                        rengor_price_final = float(0)
                                    else:
                                        post_price_info_get_json = post_price_info_get.json()
                                        rengor_price_final = float(post_price_info_get_json["UnitPrice"])
                                    if rengor_price_final != 0:
                                        customer_order_rows.append({
                                            "PartId": int(rengor_id),
                                            "OrderedQuantity": 1.0,
                                            "Price": round(float(float((int(var_uthyrd) - int(var_ater)) / 1000) * float(rengor_price_final)), 2),
                                            "WarehouseId": int(wh_id),
                                            "OrderRowType": 1,
                                            "AffectStockBalance": False
                                        })

                                customer_order_rows.append({
                                    "PartId": int(var_partid),
                                    "OrderedQuantity": 1.0,
                                    "Price": round(float(float((int(var_uthyrd) - int(var_ater)) / 1000) * float(real_price_price)), 2),
                                    "WarehouseId": int(wh_id),
                                    "OrderRowType": 1,
                                    "AffectStockBalance": True,
                                    "DeliveryReportingLocations": [
                                        {
                                            "Quantity": 1.0,
                                            "PartLocationId": int(pr_old_pl_id),
                                            "ProductRecordId": int(product_old_old_record_id)
                                        }
                                    ]
                                })
                            else:
                                customer_order_rows.append({
                                    "PartId": int(var_partid),
                                    "OrderedQuantity": 1.0,
                                    "Price": round(float(float((int(var_uthyrd) - int(var_ater)) / 1000) * float(real_price_price)), 2),
                                    "WarehouseId": int(wh_id),
                                    "OrderRowType": 1,
                                    "AffectStockBalance": True,
                                    "DeliveryReportingLocations": [
                                        {
                                            "Quantity": 1.0,
                                            "PartLocationId": int(pr_old_pl_id),
                                            "ProductRecordId": int(product_old_old_record_id)
                                        }
                                    ]
                                })
                        elif var_ater == var_uthyrd:
                            WH_url = f"https://{host}/sv/{company}/api/v1/Common/Warehouses?$filter=Code eq '{LS_huvud}'"

                            def RetryWH(s, max_tries=40):
                                counter = 0
                                while True:
                                    reportResulst = s.get(url=WH_url, verify=False)
                                    if reportResulst.status_code == 200:
                                        return reportResulst

                                    counter += 1
                                    if counter == max_tries:
                                        messagebox.showinfo("Error", f'Not able to fetch the connected customerorder row')
                                        break

                                    if reportResulst.status_code != 200:
                                        r = Retry1(s)
                                    time.sleep(0.4)

                            WH_Get = RetryWH(s)
                            WH_Get_json = WH_Get.json()
                            wh_id = int(WH_Get_json[0]["Id"])
                            part_rengor = None

                            for ef_value in artikel_ef:
                                if ef_value == f'{artikel_rengoring}':
                                    ef_url = f"https://{host}/sv/{company}/api/v1/Common/ExtraFields?$filter=ParentId eq {int(var_partid)} and Identifier eq '{ef_value}'"

                                    def RetryEFEF(s, max_tries=40):
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

                                    ef_result = RetryEFEF(s)
                                    if ef_result.text == [] or ef_result.text == "[]":
                                        pass
                                    else:
                                        ef_result_json = ef_result.json()
                                        part_rengor = str(ef_result_json[0]["StringValue"])
                            if part_rengor != None:
                                rengor_part = f"https://{host}/sv/{company}/api/v1/Inventory/Parts?$filter=PartNumber eq '{str(part_rengor)}'"

                                def RetryRENGOR(s, max_tries=40):
                                    counter = 0
                                    while True:
                                        reportResulst = s.get(url=rengor_part, verify=False)
                                        if reportResulst.status_code == 200:
                                            return reportResulst

                                        counter += 1
                                        if counter == max_tries:
                                            messagebox.showinfo("Error1", f'Did not find the part id for the cleaning part')
                                            break

                                        if reportResulst.status_code != 200:
                                            r = Retry1(s)
                                        time.sleep(0.4)

                                rengor_get = RetryRENGOR(s)
                                rengor_get_json = rengor_get.json()
                                rengor_id = int(rengor_get_json[0]["Id"])
                                rengor_unit_id = int(rengor_get_json[0]["StandardUnitId"])

                                post_price_info = f"https://{host}/sv/{company}/api/v1/Sales/CustomerOrders/GetPriceInfo"
                                json_post_price_info = {
                                    "PartId": int(rengor_id),
                                    "CustomerId": int(end_customer_id),
                                    "UnitId": int(rengor_unit_id),
                                    "QuantityInUnit": 1.0,
                                    "UseExtendedResult": True
                                }

                                def RetryPRICE(s, max_tries=40):
                                    counter = 0
                                    while True:
                                        reportResulst = s.post(url=post_price_info, json=json_post_price_info, verify=False)
                                        if reportResulst.status_code == 200:
                                            return reportResulst

                                        counter += 1
                                        if counter == max_tries:
                                            messagebox.showerror("Error", f'Couldnt fetch the price for the cleaning part')
                                            break

                                        if reportResulst.status_code != 200:
                                            r = Retry1(s)
                                        time.sleep(0.4)

                                post_price_info_get = RetryPRICE(s)
                                if post_price_info_get.text == [] or post_price_info_get.text == "[]":
                                    rengor_price_final = float(0)
                                else:
                                    post_price_info_get_json = post_price_info_get.json()
                                    rengor_price_final = float(post_price_info_get_json["UnitPrice"])
                                if rengor_price_final != 0:
                                    customer_order_rows.append({
                                        "PartId": int(rengor_id),
                                        "OrderedQuantity": 1.0,
                                        "Price": round(float(float(int(var_uthyrd) / 1000) * float(rengor_price_final)), 2),
                                        "WarehouseId": int(wh_id),
                                        "OrderRowType": 1,
                                        "AffectStockBalance": False
                                    })

                    else:
                        pass
                if customer_order_rows:
                    url_post_invoice = f"https://{host}/sv/{company}/api/v1/Sales/CustomerOrderInvoices/Create"
                    post_invoice_json = \
                        {

                              "Rows": customer_order_rows,
                              "CustomerId": int(end_customer_id),
                              "WarehouseId": int(wh_id_real),
                              "InvoiceType": int(1)
                        }

                    def RetryCOI(s, max_tries=40):
                        counter = 0
                        while True:
                            # s = requests.session()
                            r = s.post(url=url_post_invoice, json=post_invoice_json, verify=False)
                            if r.status_code == 200:
                                return r
                            counter += 1
                            if counter == max_tries:
                                messagebox.showinfo("Error", f'Not able to post the customer order invoice')
                                break
                            time.sleep(0.4)

                    cust_invoice_get = RetryCOI(s)
                    cust_invoice_get_json = cust_invoice_get.json()
                for u in my_tree_AL.get_children():
                    my_tree_AL.delete(u)
                AL_entry_ordernumber.delete(0, END)
                AL_entry_ordernumber.focus_set()
                #     float_Q = float(o)
                #     int_Q = int(float_Q)
                #     langd = str(q)
                #     partid = int(t)
                #     if int_Q <= 0:
                #         pass
                #     else:
                #         serial_numbers_w_length = f"https://{host}/sv/{company}/api/v1/Inventory/ProductRecords?$filter=PartId eq {int(partid)} and ChargeNumber eq '{langd}'&$orderby=ActualArrivalDate desc"
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
            #(cursor="")
            tom_lista = []
            update_function_AL(tom_lista)
            update_function_AL_lenght(tom_lista)
            AL_entry_ordernumber.delete(0, END)
            AL_entry_ordernumber.focus_set()
            combobox_AL.set("")
            combobox_AL_2.set("")
            AL_label_customer["text"] = ""
            AL_label_mark["text"] = "Antal markerade rader: "
            messagebox.showinfo("Info", "Återlämningen gick ok!")
            for u in my_tree_ul.get_children():
                my_tree_ul.delete(u)
            AL_entry_ordernumber.delete(0, END)
            AL_entry_recieve.delete(0, END)
            AL_entry_ordernumber.focus_set()

            # Uppdatera extra fälten på serienummer härnäst
        except Exception as e:
            #tab3.config(cursor="")
            # tom_lista = []
            # update_function_AL(tom_lista)
            # update_function_AL_lenght(tom_lista)
            # AL_entry_ordernumber.delete(0, END)
            # AL_entry_ordernumber.focus_set()
            # AL_label_customer["text"] = ""
            messagebox.showinfo("Info", e)


    AL_label_rutin = ttk.Label(tab3, text="Projektnummer", font=("Calibri", 18, "bold"))
    AL_label_rutin.grid(row=0, column=0, padx=(10, 0), pady=(2, 20), sticky=W, columnspan=2)

    # Label till ordernummer i rapportera inleverans
    AL_label_ordernumber = ttk.Label(tab3, text="Kundnummer: ", font=("Calibri", 14, "bold"))
    AL_label_ordernumber.grid(row=1, column=0, padx=(10, 0), pady=1, sticky=W)

    # Entry till ordernummer
    AL_entry_ordernumber = ttk.Entry(tab3, font=("Calibri", 14))
    AL_entry_ordernumber.grid(row=2, column=0, padx=(10, 0), pady=(0, 40), sticky=W)
    AL_entry_ordernumber.bind("<Return>", populate_treeview_AL)

    options_AL_ComboBox = ['']
    selected_AL_ComboBox = StringVar(tab1)
    selected_AL_ComboBox.set("")
    combobox_AL = ttk.Combobox(tab3, values=options_AL_ComboBox, state="normal", textvariable=selected_AL_ComboBox)

    options_AL_ComboBox_2 = ['']
    selected_AL_ComboBox_2 = StringVar(tab3)
    selected_AL_ComboBox_2.set("")
    combobox_AL_2 = ttk.Combobox(tab3, values=options_AL_ComboBox_2, state="normal", textvariable=selected_AL_ComboBox_2)


    def backend_get_new_values_ComboBox_AL(listar):
        listar = listar
        # Gör saker som uppdaterar ComboBox
        return listar


    def get_new_values_ComboBox_AL(recieve_list_1):
        recieve_list_1.append("")
        recieve_list_1.sort()
        listar = backend_get_new_values_ComboBox_AL(recieve_list_1)
        combobox_AL["values"] = listar
        # combobox_IL_2["values"] = listar


    def update_function_AL(recieve_list):
        combobox_IL.config(postcommand=get_new_values_ComboBox_AL(recieve_list))
        # combobox_IL_2.config(postcommand=get_new_values_ComboBox_IL(recieve_list))


    def backend_get_new_values_ComboBox_AL_lenght(listar):
        listar = listar
        # Gör saker som uppdaterar ComboBox
        return listar


    def get_new_values_ComboBox_AL_lenght(recieve_list_1):
        recieve_list_1.append("")
        recieve_list_1.sort()
        listar = backend_get_new_values_ComboBox_AL(recieve_list_1)
        # combobox_IL["values"] = listar
        combobox_AL_2["values"] = listar


    def update_function_AL_lenght(recieve_list):
        # combobox_IL.config(postcommand=get_new_values_ComboBox_IL(recieve_list))
        combobox_AL_2.config(postcommand=get_new_values_ComboBox_AL_lenght(recieve_list))


    def populate_treeview_AL_with_combo(events):
        try:
            # tab3.config(cursor="watch")
            # tab3.update()
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
                    customer_url = f"https://{host}/sv/{company}/api/v1/Sales/Customers?$filter=Code eq '{ordernumber}'"

                    def RetryCustomer(s, max_tries=40):
                        counter = 0
                        while True:
                            reportResulst = s.get(url=customer_url, verify=False)
                            if reportResulst.status_code == 200:
                                return reportResulst

                            counter += 1
                            if counter == max_tries:
                                messagebox.showerror("Error", f'Not able to fetch the warehouse')
                                break

                            if reportResulst.status_code != 200:
                                r = Retry1(s)
                            time.sleep(0.4)

                    customer_get = RetryCustomer(s)
                    customer_get_json = customer_get.json()
                    if customer_get_json == []:
                        tom_lista = []
                        update_function_AL(tom_lista)
                        update_function_AL_lenght(tom_lista)
                        AL_entry_ordernumber.delete(0, END)
                        AL_entry_ordernumber.focus_set()
                        AL_label_customer["text"] = ""
                        AL_label_mark["text"] = "Antal markerade rader: "
                        messagebox.showerror("Error", f'Not able to fetch the customer information')
                    else:
                        part_numbers = []
                        lengths = []
                        kundnamn = customer_get_json[0]["Name"]
                        AL_label_customer["text"] = kundnamn

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
                                        # print(iora)
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
                                        part_numbers.append(str(part_get_json[0]["PartNumber"]))
                                        partnumber = str(part_get_json[0]["PartNumber"])
                                        length = str(pr_get_json[0]["ChargeNumber"])
                                        lengths.append(str(pr_get_json[0]["ChargeNumber"]))
                                        if str(combobox_AL.get()) == "" and str(combobox_AL_2.get()) == "":
                                            my_tree_AL.insert('', 'end', values=(
                                                0, pr_get_json[0]["SerialNumber"], part_get_json[0]["PartNumber"], part_get_json[0]["Description"], pr_get_json[0]["ChargeNumber"], pr_get_json[0]["ChargeNumber"], 1, part_id, iora['ProductRecordId'],
                                                iora["Quantity"], iora["PartLocationId"]))
                                        elif str(combobox_AL.get()) != "" and str(combobox_AL_2.get()) == "":
                                            if str(combobox_AL.get()) == str(partnumber):
                                                my_tree_AL.insert('', 'end', values=(
                                                    0, pr_get_json[0]["SerialNumber"], part_get_json[0]["PartNumber"], part_get_json[0]["Description"], pr_get_json[0]["ChargeNumber"], pr_get_json[0]["ChargeNumber"], 1, part_id,
                                                    iora['ProductRecordId'],
                                                    iora["Quantity"], iora["PartLocationId"]))
                                            else:
                                                pass
                                        elif str(combobox_AL.get()) == "" and str(combobox_AL_2.get()) != "":
                                            if str(combobox_AL_2.get()) == str(length):
                                                my_tree_AL.insert('', 'end', values=(
                                                    0, pr_get_json[0]["SerialNumber"], part_get_json[0]["PartNumber"], part_get_json[0]["Description"], pr_get_json[0]["ChargeNumber"], pr_get_json[0]["ChargeNumber"], 1, part_id,
                                                    iora['ProductRecordId'],
                                                    iora["Quantity"], iora["PartLocationId"]))
                                            else:
                                                pass
                                        elif str(combobox_AL_2.get()) != "" and str(combobox_AL.get()) != "":
                                            if str(combobox_AL.get()) == str(partnumber) and str(combobox_AL_2.get()) == str(length):
                                                my_tree_AL.insert('', 'end', values=(
                                                    0, pr_get_json[0]["SerialNumber"], part_get_json[0]["PartNumber"], part_get_json[0]["Description"], pr_get_json[0]["ChargeNumber"], pr_get_json[0]["ChargeNumber"], 1, part_id,
                                                    iora['ProductRecordId'],
                                                    iora["Quantity"], iora["PartLocationId"]))
                                            else:
                                                pass

                        part_numbers.sort()
                        partnumbers = list(set(part_numbers))
                        lengths.sort()
                        length_list = list(set(lengths))
                        update_function_AL(partnumbers)
                        update_function_AL_lenght(length_list)
            # tab3.config(cursor="")

        except Exception as e:
            # (cursor="")
            messagebox.showerror("Error", f"Issues with populating the treeview {e}")


    combobox_AL.grid(row=2, column=0, padx=(10, 0), pady=1, sticky=SW, ipadx=10)
    combobox_AL_2.grid(row=2, column=3, padx=(30, 0), pady=1, sticky=SE, ipadx=10)

    combobox_AL.bind("<<ComboboxSelected>>", populate_treeview_AL_with_combo)
    combobox_AL_2.bind("<<ComboboxSelected>>", populate_treeview_AL_with_combo)

    def AL_mark_as_return():
        selected_items = my_tree_AL.selection()
        for itemss in selected_items:
            items = my_tree_AL.item(itemss)
            values = items.get("values")
            my_tree_AL.set(itemss, "#1", int(1))


    AL_buttom_mark = ttk.Button(tab3, text="Markera som återlämnade", command=AL_mark_as_return)
    AL_buttom_mark.grid(row=4, column=1, padx=(10, 0), pady=(0, 5), sticky=W, ipadx=30)

    AL_label_mark = ttk.Label(tab3, text="Antal markerade rader: ", font=('Helvetica', 12, "bold"))
    AL_label_mark.grid(row=4, column=2, padx=(10, 0), pady=(0, 5), sticky=W, ipadx=30)

    AL_label_customer = ttk.Label(tab3, text="", font=('Helvetica', 12, "bold"))
    AL_label_customer.grid(row=1, column=1, rowspan=2, padx=(5, 0), pady=(0, 5), sticky=W, ipadx=30)

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
    my_tree_AL.column("Serienummer", anchor=W, width=160)
    my_tree_AL.column("Artikelnr.", anchor=W, width=110)
    my_tree_AL.column("Benämning", anchor=W, width=200)
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
    AL_label_recieve.grid(row=5, column=0, padx=(10, 0), pady=(0, 2), sticky=W)
    AL_entry_recieve = ttk.Entry(tab3, font=("Calibri", 14))
    AL_entry_recieve.grid(row=6, column=0, padx=(10, 0), pady=(0, 50), sticky=W)

    var = IntVar(value=0)
    var2 = IntVar(value=0)
    c1 = ttk.Checkbutton(tab3, text='Återlämna', onvalue=1, offvalue=0, variable=var)
    c1.grid(row=5, column=1, padx=(10, 0), pady=(0, 2), sticky=S+W)
    #c1.bind('<ButtonRelease-1>', get_state)
    c2 = ttk.Checkbutton(tab3, text='Rengör', onvalue=1, offvalue=0, variable=var2)
    c2.grid(row=6, column=1, padx=(10, 0), pady=(0, 2), sticky=N+W)

    # UL_label_length = ttk.Label(tab2, text="Längd: ", font=("Calibri", 14, "bold"))
    # UL_label_length.grid(row=4, column=1, padx=(2, 0), pady=(0, 2), sticky=W)
    # UL_entry_length = ttk.Entry(tab2, font=("Calibri", 14))
    # UL_entry_length.grid(row=5, column=1, padx=(2, 0), pady=(0, 50), sticky=W)

    AL_button_edit = ttk.Button(tab3, text="Uppdatera", style="my.TButton", command=update_record_AL)
    AL_button_edit.grid(row=6, column=2, padx=(2, 0), pady=(0, 50), ipadx=30, sticky=W)
    AL_button_recieve = ttk.Button(tab3, text="Återlämna", style="my.TButton", command=create_invoice)
    AL_button_recieve.grid(row=6, column=3, padx=(2, 0), pady=(0, 50), ipadx=30, sticky=W)

    my_tree_AL.bind('<ButtonRelease-1>', select_record_AL)


    def split_serialnumbers():
        try:
            serialnumber = str(SPL_entry_ordernumber.get())

            langd = []
            for u in my_tree_SPL.get_children():
                children = my_tree_SPL.item(u, "values")
                langd.append(int(children[0]))

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
                pr_url = f"https://{host}/sv/{company}/api/v1/Inventory/ProductRecords?$filter=SerialNumber eq '{serialnumber}'"

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
                pr_id = int(pr_get_json[0]["Id"])
                pr_langd = str(pr_get_json[0]["ChargeNumber"])
                part_id = int(pr_get_json[0]["PartId"])

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
                        ef_url = f"https://{host}/sv/{company}/api/v1/Common/ExtraFields?$filter=ParentId eq {pr_id} and Identifier eq '{ef_value}'"

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
                        if ef_result.text == [] or ef_result.text == "[]":
                            pass
                        else:
                            ef_result_json = ef_result.json()
                            SERTILLG = int(ef_result_json[0]["IntegerValue"])
                    elif ef_value == f'{serienummer_avskrivningskonto}':
                        ef_url = f"https://{host}/sv/{company}/api/v1/Common/ExtraFields?$filter=ParentId eq {pr_id} and Identifier eq '{ef_value}'"

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
                        if ef_result.text == [] or ef_result.text == "[]":
                            pass
                        else:
                            ef_result_json = ef_result.json()
                            SERAVSKR = int(ef_result_json[0]["IntegerValue"])
                    elif ef_value == f'{serienummer_anskaffningsvarde}':
                        ef_url = f"https://{host}/sv/{company}/api/v1/Common/ExtraFields?$filter=ParentId eq {pr_id} and Identifier eq '{ef_value}'"

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
                        if ef_result.text == [] or ef_result.text == "[]":
                            pass
                        else:
                            ef_result_json = ef_result.json()
                            SERANSKA = float(ef_result_json[0]["DecimalValue"])
                    elif ef_value == f'{serienummer_restvarde}':
                        ef_url = f"https://{host}/sv/{company}/api/v1/Common/ExtraFields?$filter=ParentId eq {pr_id} and Identifier eq '{ef_value}'"

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
                        if ef_result.text == [] or ef_result.text == "[]":
                            pass
                        else:
                            ef_result_json = ef_result.json()
                            SERRESTV = float(ef_result_json[0]["DecimalValue"])
                    elif ef_value == f'{serienummer_avskriven}':
                        ef_url = f"https://{host}/sv/{company}/api/v1/Common/ExtraFields?$filter=ParentId eq {pr_id} and Identifier eq '{ef_value}'"

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
                        if ef_result.text == [] or ef_result.text == "[]":
                            pass
                        else:
                            ef_result_json = ef_result.json()
                            SERAVSKREN = str(ef_result_json[0]["StringValue"])
                    elif ef_value == f'{serienummer_avskrivningstid}':
                        ef_url = f"https://{host}/sv/{company}/api/v1/Common/ExtraFields?$filter=ParentId eq {pr_id} and Identifier eq '{ef_value}'"

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
                        if ef_result.text == [] or ef_result.text == "[]":
                            pass
                        else:
                            ef_result_json = ef_result.json()
                            SERAVSTID = int(ef_result_json[0]["IntegerValue"])
                    elif ef_value == f'{serienummer_klar}':
                        ef_url = f"https://{host}/sv/{company}/api/v1/Common/ExtraFields?$filter=ParentId eq {pr_id} and Identifier eq '{ef_value}'"

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
                        if ef_result.text == [] or ef_result.text == "[]":
                            pass
                        else:
                            ef_result_json = ef_result.json()
                            SERKLAR = (ef_result_json[0]["DateOnlyValue"])
                            SERKLAR = str(SERKLAR[0:10])
                    elif ef_value == f'{serienummer_utrangeratpris}':
                        ef_url = f"https://{host}/sv/{company}/api/v1/Common/ExtraFields?$filter=ParentId eq {pr_id} and Identifier eq '{ef_value}'"

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
                        if ef_result.text == [] or ef_result.text == "[]":
                            pass
                        else:
                            ef_result_json = ef_result.json()
                            SERUTRANG = float(ef_result_json[0]["DecimalValue"])
                    elif ef_value == f'{serienummer_utrangeratdatum}':
                        ef_url = f"https://{host}/sv/{company}/api/v1/Common/ExtraFields?$filter=ParentId eq {pr_id} and Identifier eq '{ef_value}'"

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
                        if ef_result.text == [] or ef_result.text == "[]":
                            pass
                        else:
                            ef_result_json = ef_result.json()
                            SERUTRANGD = (ef_result_json[0]["DateOnlyValue"])
                            SERUTRANGD = str(SERUTRANGD[0:10])

                for u in my_tree_SPL.get_children():
                    children = my_tree_SPL.item(u, "values")
                    new_length = int(children[0])

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
                    nextserial = int(next_serial_number_string[3:])
                    nextserial_final = nextserial + 1

                    WH_url = f"https://{host}/sv/{company}/api/v1/Common/Warehouses?$filter=Code eq '{LS_huvud}'"

                    def RetryWH(s, max_tries=40):
                        counter = 0
                        while True:
                            reportResulst = s.get(url=WH_url, verify=False)
                            if reportResulst.status_code == 200:
                                return reportResulst

                            counter += 1
                            if counter == max_tries:
                                messagebox.showinfo("Error", f'Not able to fetch the connected customerorder row')
                                break

                            if reportResulst.status_code != 200:
                                r = Retry1(s)
                            time.sleep(0.4)

                    WH_Get = RetryWH(s)
                    WH_Get_json = WH_Get.json()
                    wh_id = int(WH_Get_json[0]["Id"])

                    pl_id_url = f"https://{host}/sv/{company}/api/v1/Inventory/PartLocations?$filter=PartId eq {int(part_id)} and WarehouseId eq {int(wh_id)} and Name eq '{lagerplats}' and LifeCycleState eq 10&$TOP=1"

                    def RetryPL_ID(s, max_tries=40):
                        counter = 0
                        while True:
                            reportResulst = s.get(url=pl_id_url, verify=False)
                            if reportResulst.status_code == 200:
                                return reportResulst

                            counter += 1
                            if counter == max_tries:
                                messagebox.showinfo("Error", f'Not able to fetch the connected customerorder row')
                                break

                            if reportResulst.status_code != 200:
                                r = Retry1(s)
                            time.sleep(0.4)

                    invent_pr_json = None
                    pl_id_get = RetryPL_ID(s)
                    invent_pr = f"https://{host}/sv/{company}/api/v1/Inventory/Parts/ReportStockCount"
                    if pl_id_get.text == [] or pl_id_get.text == "[]":
                        invent_pr_json = {
                            "PartId": int(part_id),
                            "WarehouseId": int(wh_id),
                            "Name": f"{lagerplats}",
                            "Balance": 1.0,
                            "SerialNumber": "SER" + f"{nextserial_final}"
                        }
                    elif pl_id_get.text != [] or pl_id_get.text != "[]":
                        pl_id_json = pl_id_get.json()
                        pl_id = int(pl_id_json[0]["Id"])
                        invent_pr_json = {
                            "PartId": int(part_id),
                            "WarehouseId": int(wh_id),
                            "PartLocationId": int(pl_id),
                            "Balance": (float(1.0)),
                            "SerialNumber": "SER" + f"{nextserial_final}"
                        }

                    def RetryInvent(s, max_tries=40):
                        counter = 0
                        while True:
                            reportResulst = s.post(url=invent_pr, json=invent_pr_json, verify=False)
                            if reportResulst.status_code == 200:
                                return reportResulst

                            counter += 1
                            if counter == max_tries:
                                messagebox.showerror("Error", f'Not able to update the charge numbers, since the row has been reported arrival, \nplease update the charge numbers manually')
                                break

                            if reportResulst.status_code != 200:
                                r = Retry1(s)
                            time.sleep(0.4)

                    invent_update = RetryInvent(s)
                    invent_update_json = invent_update.json()

                    pr_pr = f"https://{host}/sv/{company}/api/v1/Inventory/ProductRecords?$filter=SerialNumber eq 'SER{nextserial_final}'"

                    def RetryPRPR(s, max_tries=40):
                        counter = 0
                        while True:
                            reportResulst = s.get(url=pr_pr, verify=False)
                            if reportResulst.status_code == 200:
                                return reportResulst

                            counter += 1
                            if counter == max_tries:
                                messagebox.showinfo("Error", f'Not able to find the starting product record')
                                break

                            if reportResulst.status_code != 200:
                                r = Retry1(s)
                            time.sleep(0.4)

                    pr_pr_get = RetryPRPR(s)
                    pr_pr_get_json = pr_pr_get.json()
                    product_new_record_id = int(pr_pr_get_json[0]["Id"])



                    url_product_record_update = f"https://{host}/sv/{company}/api/v1/Inventory/ProductRecords/SetProperties"
                    json_product_record = {
                        "ProductRecordId": int(product_new_record_id),
                        "ChargeNumber": {"Value": str(new_length)}
                    }

                    def RetryZZ(s, max_tries=40):
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

                    product_record_update = RetryZZ(s)
                    product_record_update_json = product_record_update.json()

                    # serienummer_tillgangskonto = parser['logics_EF']['serienummer_tillgangskonto']
                    # serienummer_avskrivningskonto = parser['logics_EF']['serienummer_avskrivningskonto']
                    # serienummer_anskaffningsvarde = parser['logics_EF']['serienummer_anskaffningsvarde']
                    # serienummer_restvarde = parser['logics_EF']['serienummer_restvarde']
                    # serienummer_avskriven = parser['logics_EF']['serienummer_avskriven']
                    # serienummer_avskrivningstid = parser['logics_EF']['serienummer_avskrivningstid']
                    # serienummer_klar = parser['logics_EF']['serienummer_klar']
                    # serienummer_utrangeratpris = parser['logics_EF']['serienummer_utrangeratpris']
                    # serienummer_utrangeratdatum = parser['logics_EF']['serienummer_utrangeratdatum']
                    anskaffningsvarde_ny = round(float(SERANSKA) * float(1 - ((int(pr_langd) - int(new_length)) / int(pr_langd))), 2)
                    #anskaffningsvarde_gammal = round(float(SERANSKA) * float(1 - ((int(var_uthyrd) - int(var_ater)) / int(var_uthyrd))), 2)
                    restvarde_ny = round(float(SERRESTV) * float(1 - ((int(pr_langd) - int(new_length)) / int(pr_langd))), 2)
                    # estvarde_gammal = round(float(SERRESTV) * float(1 - ((int(var_uthyrd) - int(var_ater)) / int(var_uthyrd))), 2)

                    lista_ef_ny_pr = []
                    for j in inleverans_ef_sn:
                        date_now = datetime.now().date()

                        if j == serienummer_anskaffningsvarde:
                            lista_ef_ny_pr.append({"Identifier": serienummer_anskaffningsvarde, "DecimalValue": float(anskaffningsvarde_ny)})
                        elif j == serienummer_restvarde:
                            lista_ef_ny_pr.append({"Identifier": serienummer_restvarde, "DecimalValue": float(restvarde_ny)})
                        elif j == serienummer_avskrivningskonto:
                            lista_ef_ny_pr.append({"Identifier": serienummer_avskrivningskonto, "IntegerValue": int(SERAVSKR)})
                        elif j == serienummer_klar:
                            lista_ef_ny_pr.append({"Identifier": serienummer_klar, "DateOnlyValue": f"{str(SERKLAR)}"})
                        elif j == serienummer_avskrivningstid:
                            lista_ef_ny_pr.append({"Identifier": serienummer_avskrivningstid, "IntegerValue": int(SERAVSTID)})
                        elif j == serienummer_tillgangskonto:
                            lista_ef_ny_pr.append({"Identifier": serienummer_tillgangskonto, "IntegerValue": int(SERTILLG)})

                    url_ef_value_sn = f"https://{host}/sv/{company}/api/v1/Common/Commands/SetExtraFieldValues"
                    json_ef_values = {
                        "EntityId": int(product_new_record_id),
                        "EntityType": 0,
                        "Values": lista_ef_ny_pr
                    }

                    def Retry7(s, max_tries=40):
                        counter = 0
                        while True:
                            reportResulst = s.post(url=url_ef_value_sn, json=json_ef_values, verify=False)
                            if reportResulst.status_code == 200:
                                return reportResulst

                            counter += 1
                            if counter == max_tries:
                                messagebox.showerror("Error", f'Was not able to set extra field values on product record id {product_new_record_id}')
                                break

                            if reportResulst.status_code != 200:
                                r = Retry1(s)
                            time.sleep(0.4)

                    ef_values_update = Retry7(s)
                    ef_values_update_json = ef_values_update.json()
                summa_langd_str = str(sum(langd))
                total_langd = int(summa_langd_str)

                anskaffningsvarde_gammal = round(float(SERANSKA) * float((int(pr_langd) - float(total_langd)) / int(pr_langd)), 2)
                #restvarde_ny = round(float(SERRESTV) * float(1 - ((int(pr_langd) - int(new_length)) / int(pr_langd))), 2)
                restvarde_gammal = round(float(SERRESTV) * (float((int(pr_langd) - float(total_langd)) / int(pr_langd))), 2)

                lista_ef_ny_pr_1 = []
                for j in inleverans_ef_sn:
                    date_now = datetime.now().date()

                    if j == serienummer_anskaffningsvarde:
                        lista_ef_ny_pr_1.append({"Identifier": serienummer_anskaffningsvarde, "DecimalValue": float(anskaffningsvarde_gammal)})
                    elif j == serienummer_restvarde:
                        lista_ef_ny_pr_1.append({"Identifier": serienummer_restvarde, "DecimalValue": float(restvarde_gammal)})
                    elif j == serienummer_avskrivningskonto:
                        lista_ef_ny_pr_1.append({"Identifier": serienummer_avskrivningskonto, "IntegerValue": int(SERAVSKR)})
                    elif j == serienummer_klar:
                        lista_ef_ny_pr_1.append({"Identifier": serienummer_klar, "DateOnlyValue": f"{str(SERKLAR)}"})
                    elif j == serienummer_avskrivningstid:
                        lista_ef_ny_pr_1.append({"Identifier": serienummer_avskrivningstid, "IntegerValue": int(SERAVSTID)})
                    elif j == serienummer_tillgangskonto:
                        lista_ef_ny_pr_1.append({"Identifier": serienummer_tillgangskonto, "IntegerValue": int(SERTILLG)})
                url_product_record_update = f"https://{host}/sv/{company}/api/v1/Inventory/ProductRecords/SetProperties"
                json_product_record = {
                    "ProductRecordId": int(pr_id),
                    "ChargeNumber": {"Value": f"{int(int(pr_langd)-float(total_langd))}"}
                }
                def RetryZZ(s, max_tries=40):
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

                product_record_update = RetryZZ(s)
                product_record_update_json = product_record_update.json()

                url_ef_value_sn = f"https://{host}/sv/{company}/api/v1/Common/Commands/SetExtraFieldValues"
                json_ef_values = {
                    "EntityId": int(pr_id),
                    "EntityType": 0,
                    "Values": lista_ef_ny_pr_1
                }

                def Retry7(s, max_tries=40):
                    counter = 0
                    while True:
                        reportResulst = s.post(url=url_ef_value_sn, json=json_ef_values, verify=False)
                        if reportResulst.status_code == 200:
                            return reportResulst

                        counter += 1
                        if counter == max_tries:
                            messagebox.showerror("Error", f'Was not able to set extra field values on product record id {product_new_record_id}')
                            break

                        if reportResulst.status_code != 200:
                            r = Retry1(s)
                        time.sleep(0.4)

                ef_values_update = Retry7(s)
                ef_values_update_json = ef_values_update.json()

                for u in my_tree_SPL.get_children():
                    my_tree_SPL.delete(u)
                SPL_entry_ordernumber.delete(0, END)
                SPL_entry_langd.delete(0, END)
                SPL_entry_ordernumber.focus_set()
                SPL_label_langd_input["text"] = ""
                SPL_label_aterstaende_input["text"] = ""
                messagebox.showinfo("Info", f'Splitt av serienummer gick ok!')
        except Exception as e:
            messagebox.showerror("Error", f"Issues with updating the record {e}")

            # FÄRDIG


    def populate_treeview_SPL(events):
        try:
            for u in my_tree_SPL.get_children():
                my_tree_SPL.delete(u)
            ordernumber = str(SPL_entry_ordernumber.get())
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


                wh_url = f"https://{host}/sv/{company}/api/v1/Common/Warehouses?$filter=Code eq '{LS_huvud}'"

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
                    # wh_id = int(wh_get_json[0]["Id"])
                    #
                    # pl_url = f"https://{host}/sv/{company}/api/v1/Inventory/PartLocations?$filter=WarehouseId eq {wh_id} and Name eq '{ordernumber}' and LifeCycleState eq 10 and Balance gt 0&$expand=PartLocationProductRecords"
                    #
                    # def Retry900(s, max_tries=40):
                    #     counter = 0
                    #     while True:
                    #         reportResulst = s.get(url=pl_url, verify=False)
                    #         if reportResulst.status_code == 200:
                    #             return reportResulst
                    #
                    #         counter += 1
                    #         if counter == max_tries:
                    #             messagebox.showerror("Error", f'Not able to fetch the part information on the parts included in the customer order')
                    #             break
                    #
                    #         if reportResulst.status_code != 200:
                    #             r = Retry1(s)
                    #         time.sleep(0.4)
                    #
                    # pl_get = Retry900(s)
                    # if pl_get == []:
                    #     messagebox.showerror("Error", f'Did not find any rows for the specific project')
                    # else:
                    # pl_get_json = pl_get.json()
                    # for pr_bals in pl_get_json:
                    #     for iora in pr_bals["PartLocationProductRecords"]:
                    #         if iora["Quantity"] > 0:
                                #print(iora)
                    pr_url = f"https://{host}/sv/{company}/api/v1/Inventory/ProductRecords?$filter=SerialNumber eq '{str(SPL_entry_ordernumber.get())}'"

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
                    part_id = str(pr_get_json[0]["ChargeNumber"])
                    # part_url = f"https://{host}/sv/{company}/api/v1/Inventory/Parts?$filter=Id eq {part_id}"
                    #
                    # def Retry10001(s, max_tries=40):
                    #     counter = 0
                    #     while True:
                    #         reportResulst = s.get(url=part_url, verify=False)
                    #         if reportResulst.status_code == 200:
                    #             return reportResulst
                    #
                    #         counter += 1
                    #         if counter == max_tries:
                    #             messagebox.showerror("Error", f'Not able to fetch information regarding the productrecord')
                    #             break
                    #
                    #         if reportResulst.status_code != 200:
                    #             r = Retry1(s)
                    #         time.sleep(0.4)
                    #
                    # part_get = Retry10001(s)
                    # part_get_json = part_get.json()

                    #my_tree_SPL.insert('', 'end', values=(part_id))
                    SPL_label_langd_input["text"] = part_id
                    SPL_label_aterstaende_input["text"] = part_id
                    SPL_entry_langd.focus_set()
        except Exception as e:
            messagebox.showerror("Error", f"Issues with updating the labels {e}")

    def populate_treeview_SPL_real_pop():
        try:
            langd = str(SPL_entry_langd.get())
            ordernumber = str(SPL_entry_ordernumber.get())
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
            part_id = 0
            if r_fel == None or r_fel == "None":
                messagebox.showerror("Error", f'Not able to login to the API')
            else:

                wh_url = f"https://{host}/sv/{company}/api/v1/Common/Warehouses?$filter=Code eq '{LS_huvud}'"

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
                    # wh_id = int(wh_get_json[0]["Id"])
                    #
                    # pl_url = f"https://{host}/sv/{company}/api/v1/Inventory/PartLocations?$filter=WarehouseId eq {wh_id} and Name eq '{ordernumber}' and LifeCycleState eq 10 and Balance gt 0&$expand=PartLocationProductRecords"
                    #
                    # def Retry900(s, max_tries=40):
                    #     counter = 0
                    #     while True:
                    #         reportResulst = s.get(url=pl_url, verify=False)
                    #         if reportResulst.status_code == 200:
                    #             return reportResulst
                    #
                    #         counter += 1
                    #         if counter == max_tries:
                    #             messagebox.showerror("Error", f'Not able to fetch the part information on the parts included in the customer order')
                    #             break
                    #
                    #         if reportResulst.status_code != 200:
                    #             r = Retry1(s)
                    #         time.sleep(0.4)
                    #
                    # pl_get = Retry900(s)
                    # if pl_get == []:
                    #     messagebox.showerror("Error", f'Did not find any rows for the specific project')
                    # else:
                    # pl_get_json = pl_get.json()
                    # for pr_bals in pl_get_json:
                    #     for iora in pr_bals["PartLocationProductRecords"]:
                    #         if iora["Quantity"] > 0:
                    # print(iora)
                    pr_url = f"https://{host}/sv/{company}/api/v1/Inventory/ProductRecords?$filter=SerialNumber eq '{str(SPL_entry_ordernumber.get())}'"

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
                    part_id = str(pr_get_json[0]["ChargeNumber"])
                    # part_url = f"https://{host}/sv/{company}/api/v1/Inventory/Parts?$filter=Id eq {part_id}"
                    #
                    # def Retry10001(s, max_tries=40):
                    #     counter = 0
                    #     while True:
                    #         reportResulst = s.get(url=part_url, verify=False)
                    #         if reportResulst.status_code == 200:
                    #             return reportResulst
                    #
                    #         counter += 1
                    #         if counter == max_tries:
                    #             messagebox.showerror("Error", f'Not able to fetch information regarding the productrecord')
                    #             break
                    #
                    #         if reportResulst.status_code != 200:
                    #             r = Retry1(s)
                    #         time.sleep(0.4)
                    #
                    # part_get = Retry10001(s)
                    # part_get_json = part_get.json()

                    # my_tree_SPL.insert('', 'end', values=(part_id))
                    SPL_label_langd_input["text"] = part_id


            my_tree_SPL.insert('', 'end', values=(langd))
            langd_tot = []
            for u in my_tree_SPL.get_children():
                children = my_tree_SPL.item(u, "values")
                langd_tot.append(int(children[0]))

            summan_av = int(sum(langd_tot))
            aterstaende = int(part_id)-summan_av
            SPL_label_aterstaende_input["text"] = aterstaende
            SPL_entry_langd.delete(0, END)
            SPL_entry_langd.focus_set()

        except Exception as e:
            messagebox.showerror("Error", f"Issues with populating the treeview {e}")
    # TAB 4 Design!

    SPL_label_rutin = ttk.Label(tab4, text="Split av serienummer", font=("Calibri", 18, "bold"))
    SPL_label_rutin.grid(row=0, column=0, padx=(10, 0), pady=(2, 20), sticky=W, columnspan=2)

    # Label till ordernummer i rapportera inleverans
    SPL_label_ordernumber = ttk.Label(tab4, text="Serienummer: ", font=("Calibri", 14, "bold"))
    SPL_label_ordernumber.grid(row=1, column=0, padx=(10, 0), pady=1, sticky=W)

    # Entry till ordernummer
    SPL_entry_ordernumber = ttk.Entry(tab4, font=("Calibri", 14))
    SPL_entry_ordernumber.grid(row=2, column=0, padx=(10, 0), pady=(0, 20), sticky=W)
    SPL_entry_ordernumber.bind("<Return>", populate_treeview_SPL)

    # Label till ordernummer i rapportera inleverans
    SPL_label_langd = ttk.Label(tab4, text="Längd: ", font=("Calibri", 12, "bold"))
    SPL_label_langd.grid(row=3, column=0, padx=(10, 0), pady=1, sticky=W)

    SPL_label_aterstaende = ttk.Label(tab4, text="Återstående längd: ", font=("Calibri", 12, "bold"))
    SPL_label_aterstaende.grid(row=4, column=0, padx=(10, 0), pady=(0,20), sticky=W)

    SPL_label_langd_input = ttk.Label(tab4, text="           ", font=("Calibri", 12, "bold"), width=20)
    SPL_label_langd_input.grid(row=3, column=1, padx=(2, 0), pady=1, sticky=W)

    SPL_label_aterstaende_input = ttk.Label(tab4, text="          ", font=("Calibri", 12, "bold"), width=20)
    SPL_label_aterstaende_input.grid(row=4, column=1, padx=(2, 0), pady=(0, 20), sticky=W)

    # Skal till TreeView för att hämta information från plocklista
    # part_id, iora['ProductRecordId'], iora["Quantity"], iora["PartLocationId"])



    tree_frame_SPL = Frame(tab4)
    tree_frame_SPL.grid(row=5, column=0, sticky=W, columnspan=4, ipadx=390, ipady=40, pady=(0, 10), padx=(10, 0))
    tree_scroll_SPL = ttk.Scrollbar(tree_frame_SPL)
    tree_scroll_SPL.pack(side=RIGHT, fill=Y)
    my_tree_SPL = ttk.Treeview(tree_frame_SPL, style="Custom.Treeview", yscrollcommand=tree_scroll_SPL.set)
    my_tree_SPL.tag_configure("Test", background="lightgrey", font=('Helvetica', 12, "italic"))
    my_tree_SPL.tag_configure("Test1", background="white")
    tree_scroll_SPL.config(command=my_tree_SPL.yview)
    my_tree_SPL['columns'] = ("Längd", "Serienummer", "Artikelnr.", "Benämning", "Uthyrd längd", "Återl. längd", "Rengör", "PARTID", "PR_ID", "QUANTITY", "PL_ID")
    my_tree_SPL['displaycolumns'] = ("Längd")
    my_tree_SPL.column("#0", width=1, minwidth=1, stretch=0)
    my_tree_SPL.column("Längd", anchor=W, width=100)
    my_tree_SPL.column("Serienummer", anchor=W, width=130)
    my_tree_SPL.column("Artikelnr.", anchor=W, width=110)
    my_tree_SPL.column("Benämning", anchor=W, width=230)
    my_tree_SPL.column("Uthyrd längd", anchor=W, width=110)
    my_tree_SPL.column("Återl. längd", anchor=W, width=110)
    my_tree_SPL.column("Rengör", anchor=W, width=90)
    my_tree_SPL.column("PARTID", anchor=W, width=90)
    my_tree_SPL.column("PR_ID", anchor=W, width=90)
    my_tree_SPL.column("QUANTITY", anchor=W, width=90)
    my_tree_SPL.column("PL_ID", anchor=W, width=90)

    my_tree_SPL.heading("#0", text="", anchor=W)
    my_tree_SPL.heading("Längd", text="Längd", anchor=W)
    my_tree_SPL.heading("Serienummer", text="Serienummer", anchor=W)
    my_tree_SPL.heading("Artikelnr.", text="Artikelnr", anchor=W)
    my_tree_SPL.heading("Benämning", text="Benämning", anchor=W)
    my_tree_SPL.heading("Uthyrd längd", text="Uthyrd längd", anchor=W)
    my_tree_SPL.heading("Återl. längd", text="Återl. längd", anchor=W)
    my_tree_SPL.heading("Rengör", text="Rengör", anchor=W)
    my_tree_SPL.heading("PARTID", text="PARTID", anchor=W)
    my_tree_SPL.heading("PR_ID", text="PR_ID", anchor=W)
    my_tree_SPL.heading("QUANTITY", text="QUANTITY", anchor=W)
    my_tree_SPL.heading("PL_ID", text="PL_ID", anchor=W)
    my_tree_SPL.pack(fill='both', expand=True)

    # def treeview_sort_column(my_tree_SPL, col, reverse):
    #     l = [(my_tree_SPL.set(k, col), k) for k in my_tree_SPL.get_children('')]
    #     l.sort(reverse=reverse)
    #
    #     # rearrange items in sorted positions
    #     for index, (val, k) in enumerate(l):
    #         my_tree_SPL.move(k, '', index)
    #
    #     # reverse sort next time
    #     my_tree_SPL.heading(col, command=lambda: \
    #         treeview_sort_column(my_tree_SPL, col, not reverse))
    #
    #
    # for col in my_tree_SPL['columns']:
    #     my_tree_SPL.heading(col, text=col, command=lambda: \
    #         treeview_sort_column(my_tree_SPL, col, False))

    SPL_label_langd_label = ttk.Label(tab4, text="Splitt-längd:", font=("Calibri", 12, "bold"))
    SPL_label_langd_label.grid(row=7, column=0, padx=(10, 0), pady=1, sticky=W)

    SPL_entry_langd = ttk.Entry(tab4, font=("Calibri", 14))
    SPL_entry_langd.grid(row=8, column=0, padx=(10, 0), pady=(0, 15), sticky=W)
    SPL_entry_langd.bind("<Return>", populate_treeview_AL)

    SPL_button_lagg_till = ttk.Button(tab4, text="Lägg till", style="my.TButton", command=populate_treeview_SPL_real_pop)
    SPL_button_lagg_till.grid(row=9, column=0, padx=(10, 0), pady=(0, 5), ipadx=30, sticky=W)

    SPL_button_edit = ttk.Button(tab4, text="Splitta", style="my.TButton", command=split_serialnumbers)
    SPL_button_edit.grid(row=7, column=2, padx=(2, 0), pady=(0, 5), ipadx=30, sticky=W)
    SPL_button_recieve = ttk.Button(tab4, text="Avbryt", style="my.TButton", command=create_invoice)
    SPL_button_recieve.grid(row=7, column=3, padx=(2, 0), pady=(0, 5), ipadx=30, sticky=W)

    my_tree_SPL.bind('<ButtonRelease-1>', select_record_AL)





    # Style för TreeView
    style = ttk.Style()
    style.configure("TButton", padding=10, relief="flat", background="white", foreground="black", anchor="center")
    # style.theme_use("clam")
    style.configure(".", font=('Helvetica', 12), foreground="black")
    style.configure("Treeview", foreground='black', rowheight=25)
    style.configure("Treeview.Heading", foreground='black', font=('Helvetica', 12, "bold"))



    window.mainloop()
