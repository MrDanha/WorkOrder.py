from ttkwidgets import CheckboxTreeview
import tkinter as tk

root = tk.Tk()

tree = CheckboxTreeview(root, columns=['Size'])
tree.pack()




tree.insert("", "end", "1", text="1")
tree.tag_del("1","1")
tree.insert("1", "end", "11", text="11", values=[1,2,3])
tree.insert("1", "end", "12",  text="12")
tree.insert("", "end", "2", text="2")
tree.insert("2", "end", "22", text="2")


def select_record_TL(events):
    test = tree.get_checked()
    print(tree.get_checked())


tree.bind('<ButtonRelease-1>', select_record_TL)

button = tk.Button(text="Text")
button.pack()

root.mainloop()