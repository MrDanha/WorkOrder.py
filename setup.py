import sys
from cx_Freeze import setup, Executable

company_name = "Monitor ERP System AB"
product_name = "WorkOrder_BETA"



bdist_msi_options = {
"upgrade_code": "{48B079F4-B598-438D-A62A-1A238A3F9865}",
"add_to_path": False,
"initial_target_dir": r"[ProgramFilesFolder]\%s\%s’ % (company_name, product_name)"
}

build_exe_options = {
"includes": ["requests", "urllib3", "urllib", "dateutil.relativedelta"], "include_files": ["config.ini", "delivery.ico"]
}

# GUI applications require a different base on Windows
base = None
if sys.platform == "win32":
    base = "Win32GUI"

exe = Executable(script="WorkOrder.py",
base=base, icon="delivery.ico"
)

setup(name=product_name,
version="1.0.4",
description="WorkOrder_BETA_reportarrival",
executables=[exe],
options={"bdist_msi": bdist_msi_options,
      "build_exe": build_exe_options})

# py setup.py bdist_msi

# WorkOrder 48B079F4-B598-438D-A62A-1A238A3F9865