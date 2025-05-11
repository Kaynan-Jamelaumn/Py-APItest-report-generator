# Python Virtual Environment Setup and Usage

## Overview
This guide explains how to create the enviroment and run the tests.

---

## Prerequisites
- **Python**: Ensure Python 3.x is installed on your system.
- **Pip**: Ensure `pip` (Python package manager) is installed.

---

## Steps to Create and Use a Virtual Environment

### 1. Create a Virtual Environment
```bash
python -m venv venv
```

### USe virtual enviroment 
```bash
.\venv\Scripts\activate
```

### Install Dependencies
```bash
pip install -r requirements.txt
```

### install the py-test (since currently is still in development and a  local dependency you have to "fake install it locally")
### if you are inside this repository "."  to collect the PyTestDocx
```bash
pip install -e . 

```


### Run the tests 
```bash
pytx  --test-dir <path-to-your-test-directory>

```

