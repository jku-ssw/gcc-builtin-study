import sqlite3
import os
conn = sqlite3.connect(os.path.join(os.path.dirname(__file__), "../../database.db"))
c = conn.cursor()
current_dir = os.path.dirname(__file__)


def print_query_as_command(command, query, roundn=False, percentage=False):
    print_as_command(command, c.execute(query).fetchone()[0], roundn, percentage)

def is_float(s):
    try: 
        float(s)
        return True
    except ValueError:
        return False

def is_int(s):
    try: 
        int(s)
        return True
    except ValueError:
        return False

def print_as_command(command, content, roundn=False, percentage=False):
    formatted_content = content
    if roundn:
        formatted_content = '%.0f' % formatted_content
    elif is_int(formatted_content):
        formatted_content = '{:,.0f}'.format(formatted_content)        
    elif is_float(formatted_content):
        formatted_content = '{:,.1f}'.format(formatted_content)
    if percentage:
        formatted_content = formatted_content + '\%'
    print(('\\newcommand{\\%s}[0]{%s}') % (command, formatted_content, ))

def escape_latex(str):
    return str.replace('#', '\#').replace('$', '\$').replace('_', '\_')

def print_tabular_start(name, caption, columns=None, nr_projects=None, columnstext=None):
    if columns is not None and columnstext is not None:
        print("cannot use both nr of columns and columntext!")
    if nr_projects is None or nr_projects == 1:
        append = ''
    else:
        append = ' (with at least ' + str(nr_projects) + ' projects using them)'
    print("\\newcommand{\\%s}[0]{" % name)
    print("\captionof{table}{%s}" % (caption + append,))
    print("\\begin{tabular}{", end='')
    if columns is not None:
        print("l", end='')
        for i in range(columns-1): print(" l", end='')
    else:
        print(columnstext)
    print("}")
    print("\\toprule{}")

def print_tabular_end(label):
    print("""\\bottomrule{}
\\end{tabular}
\\label{%s}}""" % (label,))

def print_table_start(name, columns, caption, nr_projects=None):
    if nr_projects is None or nr_projects == 1:
        append = ''
    else:
        append = ' (with at least ' + str(nr_projects) + ' projects using them)'
    print("\\newcommand{\\%s}[0]{" % name)
    print("\\begin{table}[]")
    print("\\caption{%s}" % (caption + append))
    print("\\centering")
    print("\\begin{tabular}{l", end='')
    for i in range(columns-1): print("|l", end='')
    print("}")

def print_table_end(label):
    print("""\\end{tabular}
\\label{%s}
\\end{table}}""" % label)
