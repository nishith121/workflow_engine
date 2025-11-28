from setuptools import setup, find_packages

with open("requirements.txt") as f:
    install_requires = f.read().strip().split("\n")

setup(
    name="workflow_engine",
    version="1.0.0",
    description="Enterprise-grade K2-style Workflow Engine with BPMN.js Designer for Frappe",
    author="Frappe",
    author_email="developers@frappe.io",
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    install_requires=install_requires,
)
