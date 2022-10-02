import base64
import json
import os
import threading
import time
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
    parser.read(file)

    host = parser["inloggning"]['host']
    company = parser['inloggning']['company']
    username = parser['inloggning']['username']
    password = parser['inloggning']['password']

    ODBC = parser['ODBC']['DSN']

    lagerplats = parser['logics']['lagerplats']
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

    cnxn = pyodbc.connect(f"DSN={ODBC}")
    cursor = cnxn.cursor()
    customer10 = cursor.execute('''create table if not EXISTS ReadOnlyUser.anp_serienummer
                                        (
                                        Serienummer Numeric(30) NOT NULL,
                                        UNIQUE (Serienummer))
                                        ''')
    cursor.commit()
    cursor.close()

    cnxn = pyodbc.connect(f"DSN={ODBC}")
    cursor = cnxn.cursor()
    customer11 = cursor.execute('''
    BEGIN IF NOT EXISTS ( SELECT serienummer FROM ReadOnlyUser.anp_serienummer 
                   WHERE serienummer = 900000000 )
                   BEGIN
                   INSERT INTO ReadOnlyUser.anp_serienummer (serienummer) VALUES (900000000)
                   END
                   END
                                            ''')
    cursor.commit()
    cursor.close()
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
                                    messagebox.showinfo("Error", f'Not able to print the delivery note through the API\nthe delivery has been made. Please print the delivery note from Monitor or the UNC-filepath instead')
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
                                    messagebox.showinfo("Error", f'Not able to print the delivery note through the API\nthe delivery has been made. Please print the delivery note from Monitor or the UNC-filepath instead')
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
                                    messagebox.showinfo("Error", f'Not able to print the delivery note through the API\nthe delivery has been made. Please print the delivery note from Monitor or the UNC-filepath instead')
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
                                    messagebox.showinfo("Error", f'Not able to print the delivery note through the API\nthe delivery has been made. Please print the delivery note from Monitor or the UNC-filepath instead')
                                    break

                                if reportResulst.status_code != 200:
                                    r = Retry1(s)
                                time.sleep(0.4)

                        ef_result = Retry2(s)
                        ef_result_json = ef_result.json()
                        ARTREN = str(ef_result_json[0]["StringValue"])

                float_Q = float(o)
                int_Q = int(float_Q)
                cnxn = pyodbc.connect(f"DSN={ODBC}")
                cursor = cnxn.cursor()
                cursor.execute(f"""
                                       select top 1 serienummer
                                       from ReadOnlyUser.anp_serienummer
                                       order by serienummer desc
                                                                            """)

                result900 = cursor.fetchall()
                serials = []
                nextserial = int(result900[0][0])
                for next in range(int_Q):
                    nextserial += 1
                    cnxn = pyodbc.connect(f"DSN={ODBC}")
                    cursor = cnxn.cursor()
                    cursor.execute(f"""
                                                           insert into readonlyuser.anp_serienummer (serienummer) values ({nextserial})
                                                                                                """)
                    cursor.commit()
                    cursor.close()
                    serials.append(nextserial)

                serials_end = []
                for i in serials:
                    serial_keys = {
                            "SerialNumber": i,
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
    my_tree['columns'] = ("Artikelnummer", "Benämning", "Restantal", "Inlevereransantal", "Enhet", "Längd", "ID", "PARTID", "PRICE")
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
    my_tree.column("PRICE", anchor=W, width=90)

    my_tree.heading("#0", text="", anchor=W)
    my_tree.heading("Artikelnummer", text="Artikelnummer", anchor=W)
    my_tree.heading("Benämning", text="Benämning", anchor=W)
    my_tree.heading("Restantal", text="Restantal", anchor=W)
    my_tree.heading("Inlevereransantal", text="Inlevereransantal", anchor=W)
    my_tree.heading("Enhet", text="Enhet", anchor=W)
    my_tree.heading("Längd", text="Längd", anchor=W)
    my_tree.heading("ID", text="ID", anchor=W)
    my_tree.heading("PARTID", text="ID", anchor=W)
    my_tree.heading("PRICE", text="PRICE", anchor=W)
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
























    # Skal till TreeView för att hämta information från om lagerplats
    my_tree_lp123 = ttk.Treeview(tab5, columns=(
    "Artikelnummer", "Benämning", "Restkvantitet", "Batch/Serienr", "PL_ID", "PR_ID", "PART_ID", "GS1_CODE",
    "Lagerplats", "EF_VALUE"), displaycolumns=("Artikelnummer", "Benämning", "Restkvantitet", "Lagerplats"))
    my_tree_lp123.column("#0", width=0, stretch=NO)
    my_tree_lp123.column("Artikelnummer", anchor=W, width=90)
    my_tree_lp123.column("Benämning", anchor=W, width=150)
    my_tree_lp123.column("Restkvantitet", anchor=W, width=60)
    my_tree_lp123.column("Batch/Serienr", anchor=W, width=60)
    my_tree_lp123.column("PL_ID", anchor=W, width=60)
    my_tree_lp123.column("PR_ID", anchor=W, width=60)
    my_tree_lp123.column("PART_ID", anchor=W, width=60)
    my_tree_lp123.column("GS1_CODE", anchor=W, width=60)
    my_tree_lp123.column("Lagerplats", anchor=W, width=60)
    my_tree_lp123.column("EF_VALUE", anchor=W, width=60)

    my_tree_lp123.heading("#0", text="", anchor=W)
    my_tree_lp123.heading("Artikelnummer", text="PartNo", anchor=W)
    my_tree_lp123.heading("Benämning", text="Description", anchor=W)
    my_tree_lp123.heading("Restkvantitet", text="Quantity", anchor=W)
    my_tree_lp123.heading("Batch/Serienr", text="Batch or SN", anchor=W)
    my_tree_lp123.heading("PL_ID", text="PartLocationId", anchor=W)
    my_tree_lp123.heading("PR_ID", text="ProductRecordId", anchor=W)
    my_tree_lp123.heading("PART_ID", text="ProductRecordId", anchor=W)
    my_tree_lp123.heading("GS1_CODE", text="GS1_CODE", anchor=W)
    my_tree_lp123.heading("Lagerplats", text="Lagerplats", anchor=W)
    my_tree_lp123.heading("EF_VALUE", text="EF_VALUE", anchor=W)

    my_tree_lp123.grid(row=4, column=1, padx=(0, 2), sticky=W)




    canvas3 = Canvas(dev_plan, width=200, height=80, background='white')
    canvas3.grid(row=0, column=1, rowspan=3, columnspan=3, sticky=W, padx=1, pady=10)

    canvas_lp_1 = Canvas(tab2, width=900, height=80, background='white')
    canvas_lp_1.grid(row=0, column=1, rowspan=3, columnspan=3, sticky=W, padx=10, pady=10)

    # Style för TreeView
    style = ttk.Style()
    style.configure("TButton", padding=10, relief="flat", background="white", foreground="black", anchor="center")
    # style.theme_use("clam")
    style.configure(".", font=('Helvetica', 12), foreground="black")
    style.configure("Treeview", foreground='black', rowheight=25)
    style.configure("Treeview.Heading", foreground='black', font=('Helvetica', 12, "bold"))

    # Skal till TreeView för att hämta information från om lagerplats
    tree_frame = Frame(tab2)
    tree_frame.grid(row=4, column=1, ipady=80, ipadx=180, padx=10, sticky=W)
    tree_scroll = ttk.Scrollbar(tree_frame)
    tree_scroll.pack(side=RIGHT, fill=Y)
    my_tree_lp = ttk.Treeview(tree_frame, style="Custom.Treeview", yscrollcommand=tree_scroll.set, columns=("Artikelnummer", "Benämning", "Restkvantitet", "Batch/Serienr", "PL_ID", "PR_ID", "PART_ID", "GS1_CODE", "EF_VALUE"), displaycolumns=("Artikelnummer", "Benämning", "Restkvantitet", "Batch/Serienr"))
    tree_scroll.config(command=my_tree_lp.yview)
    # my_tree_lp['columns'] = ("Artikelnummer", "Benämning", "Restkvantitet", "Batchnummer", "Serienummer", "Test")
    my_tree_lp.column("#0", anchor=W, width=1, minwidth=1, stretch=0)
    my_tree_lp.column("Artikelnummer", anchor=W, width=80)
    my_tree_lp.column("Benämning", anchor=W, width=150)
    my_tree_lp.column("Restkvantitet", anchor=W, width=80)
    my_tree_lp.column("Batch/Serienr", anchor=W, width=60)
    my_tree_lp.column("PL_ID", anchor=W, width=60)
    my_tree_lp.column("PR_ID", anchor=W, width=60)
    my_tree_lp.column("PART_ID", anchor=W, width=60)
    my_tree_lp.column("GS1_CODE", anchor=W, width=60)
    my_tree_lp.column("EF_VALUE", anchor=W, width=60)

    my_tree_lp.heading("#0", text="", anchor=W)
    my_tree_lp.heading("Artikelnummer", text="PartNo", anchor=W)
    my_tree_lp.heading("Benämning", text="Description", anchor=W)
    my_tree_lp.heading("Restkvantitet", text="Quantity", anchor=W)
    my_tree_lp.heading("Batch/Serienr", text="Batch or SN", anchor=W)
    my_tree_lp.heading("PL_ID", text="PartLocationId", anchor=W)
    my_tree_lp.heading("PR_ID", text="ProductRecordId", anchor=W)
    my_tree_lp.heading("PART_ID", text="ProductRecordId", anchor=W)
    my_tree_lp.heading("GS1_CODE", text="GS1_CODE", anchor=W)
    my_tree_lp.heading("EF_VALUE", text="EF_VALUE", anchor=W)
    my_tree_lp.pack(fill='both', expand=True)
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
    my_tree_dev_plan = ttk.Treeview(dev_plan, style="Custom.Treeview",)
    my_tree_dev_plan['columns'] = ("Nr", "Namn", "Datum", "Vikt", "Volym", "Artiklar", "Rader", "Person", "Status")
    my_tree_dev_plan.column("#0", width=1, minwidth=1)
    my_tree_dev_plan.column("Nr", anchor=W, width=40)
    my_tree_dev_plan.column("Namn", anchor=W, width=165)
    my_tree_dev_plan.column("Datum", anchor=W, width=120)
    my_tree_dev_plan.column("Vikt", anchor=W, width=60)
    my_tree_dev_plan.column("Volym", anchor=W, width=80)
    my_tree_dev_plan.column("Artiklar", anchor=W, width=60)
    my_tree_dev_plan.column("Rader", anchor=W, width=60)
    my_tree_dev_plan.column("Person", anchor=W, width=80)
    my_tree_dev_plan.column("Status", anchor=W, width=70)

    my_tree_dev_plan.heading("#0", text="", anchor=W)
    my_tree_dev_plan.heading("Nr", text="PL", anchor=W)
    my_tree_dev_plan.heading("Namn", text="Cu. Name", anchor=W)
    my_tree_dev_plan.heading("Datum", text="Date", anchor=W)
    my_tree_dev_plan.heading("Vikt", text="Weight", anchor=W)
    my_tree_dev_plan.heading("Volym", text="Volume", anchor=W)
    my_tree_dev_plan.heading("Artiklar", text="Parts", anchor=W)
    my_tree_dev_plan.heading("Rader", text="Rows", anchor=W)
    my_tree_dev_plan.heading("Person", text="Picker", anchor=W)
    my_tree_dev_plan.heading("Status", text="Status", anchor=W)
    my_tree_dev_plan.grid(row=5, column=1, ipady=3, padx=10, sticky=W, columnspan=3)

    # tree_frame_plock2 = Frame(tab1)
    # tree_frame_plock2.grid(row=5, column=1, ipady=5, padx=4, sticky=W)
    # tree_scroll_plock2 = Scrollbar(tree_frame_plock2)
    # tree_scroll_plock2.pack(side=RIGHT, fill=Y)
    # my_tree1 = ttk.Treeview(tree_frame_plock2, yscrollcommand=tree_scroll_plock2.set)
    # tree_scroll_plock2.config(command=my_tree1.yview)

    my_tree_lagerplats_frame = Frame(tab4)
    my_tree_lagerplats_frame.grid(row=10, column=1, ipady=3, padx=10, sticky=W, columnspan=3)
    tree_scroll_lagerplats = ttk.Scrollbar(my_tree_lagerplats_frame)
    tree_scroll_lagerplats.pack(side=RIGHT, fill=Y)
    my_tree_lagerplats = ttk.Treeview(my_tree_lagerplats_frame, style="Custom.Treeview",yscrollcommand=tree_scroll_lagerplats.set)  # , columns=("Lagerinfo", "Saldo"), displaycolumns=("Lagerinfo", "Saldo"))
    tree_scroll_lagerplats.config(command=my_tree_lagerplats.yview)
    # Skal till TreeView lagerplats
    # my_tree_lagerplats = ttk.Treeview(tab4)
    my_tree_lagerplats['columns'] = ("Lagerinfo", "Saldo")
    my_tree_lagerplats.column("#0", width=1, minwidth=1, stretch=0)
    my_tree_lagerplats.column("Lagerinfo", anchor=W, width=200)
    my_tree_lagerplats.column("Saldo", anchor=W, width=180)
    # my_tree_lagerplats.column("Datum", anchor=W, width=100)
    # my_tree_lagerplats.column("Vikt", anchor=W, width=50)
    # my_tree_lagerplats.column("Volym", anchor=W, width=80)
    # my_tree_lagerplats.column("Artiklar", anchor=W, width=80)
    # my_tree_lagerplats.column("Rader", anchor=W, width=60)
    # my_tree_lagerplats.column("Person", anchor=W, width=80)
    # my_tree_lagerplats.column("Status", anchor=W, width=65)

    my_tree_lagerplats.heading("#0", text="", anchor=W)
    my_tree_lagerplats.heading("Lagerinfo", text="Stock info", anchor=W)
    my_tree_lagerplats.heading("Saldo", text="Quantity", anchor=W)
    # my_tree_lagerplats.heading("Datum", text="Datum", anchor=W)
    # my_tree_lagerplats.heading("Vikt", text="Vikt", anchor=W)
    # my_tree_lagerplats.heading("Volym", text="Volym", anchor=W)
    # my_tree_lagerplats.heading("Artiklar", text="Artiklar", anchor=W)
    # my_tree_lagerplats.heading("Rader", text="Rader", anchor=W)
    # my_tree_lagerplats.heading("Person", text="Plockare", anchor=W)
    # my_tree_lagerplats.heading("Status", text="Status", anchor=W)
    # my_tree_lagerplats.grid(row=10, column=1, ipady=3, padx=10, sticky=W, columnspan=3)



    # Entry till torder

    # Label till info
    Label_torder_info = Label(tab4, text=f"                                                                                                                                 \n"
                                         f"                                                                                                                                 ", font=("Calibri", 14), bg="White")
    Label_torder_info.grid(row=8, column=1, pady=20, padx=10, columnspan=1, sticky=S)

    # Label till info
    Label_torder_info1 = Label(tab4, text=f"                           ", font=("Calibri", 20), bg="White")
    Label_torder_info1.grid(row=9, column=1, pady=20, padx=10, columnspan=1, sticky=W + E)

    window.mainloop()
