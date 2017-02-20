#-----------------------------------------------------------------------------
# Name:        HelpUtils
# Purpose:    Provides general utilities for help based functions
# Author:      Aric Sanders
# Created:     3/11/2016
# License:     MIT License
#-----------------------------------------------------------------------------
""" The HelpUtils module has tools for interacting with help files. It uses pdoc for
  auto-generated help, and nb covert to change ipynb based examples to html. There is an
  error when certain extensions are activated in jupyter for nbconvert that is solved by
  changing the imports in three modules
  see https://github.com/jupyter/nbconvert/pull/370/commits/f01e44daca69f349bfdcf24aa397aa8edc7b2b53"""
#-----------------------------------------------------------------------------
# Standard Imports
import os
import inspect
import sys
import shutil
#-----------------------------------------------------------------------------
# Third Party Imports
sys.path.append(os.path.join(os.path.dirname( __file__ ), '..','..'))
try:
    import pdoc
except:
    print("Could not import pdoc, add it to the python path or install it. pip install pdoc")
try:
    from Code.Utils.Alias import *
    METHOD_ALIASES=1
except:
    print("The module pyMeasure.Code.Utils.Alias was not found")
    METHOD_ALIASES=0
    pass
try:
    from Code.Utils.Names import auto_name,change_extension
    DEFAULT_FILE_NAME=None
except:
    print("The function auto_name in pyMeasure.Code.Utils.Names was not found")
    print("Setting Default file name to New_Data_Table.txt")
    DEFAULT_FILE_NAME='New_Data_Table.txt'
    pass
#-----------------------------------------------------------------------------
# Module Constants
TESTS_DIRECTORY=os.path.join(os.path.dirname(os.path.realpath(__file__)),'Tests')
PYMEASURE_ROOT=os.path.join(os.path.dirname(os.path.realpath(__file__)),'..','..')
DOCUMENTATION_DIRECTORY=os.path.join(PYMEASURE_ROOT,"Documentation")
INDEX_HTML_PREFIX="""<html>
<head>

    <style>
          body {
    background: #fff;
    font-family: "Source Sans Pro", "Helvetica Neueue", Helvetica, sans;
    font-weight: 300;
    font-size: 16px;
    line-height: 1.6em;
    background: #fff;
    color: #000;
  }
  li {font-family: "Ubuntu Mono", "Cousine", "DejaVu Sans Mono", monospace;}
  h1 {
    font-size: 2.5em;
    line-height: 1.1em;
    margin: 0 0 .50em 0;
    font-weight: 300;

}
    </style>
</head>
<body>
<a href="./pyMeasure_Documentation.html">Documentation Home</a> |
<a href="./pyMeasure/index.html">API Documentation Home</a> |
<a href="./Reference_Index.html">Index of all Functions and Classes in pyMeasure</a>
<h1>Index</h1>
<ol>"""
INDEX_HTML_POSTFIX="""</ol></body></html>"""
#-----------------------------------------------------------------------------
# Module Functions
def return_help(object):
    """Returns an html help page autogenerated by the pdoc module for any live object"""
    module=inspect.getmodule(object).__name__
    html_text=pdoc.html(module_name=module,allsubmodules=True)
    return html_text

def create_help_page(module,output_format='html',file_path=None):
    """Uses the pdoc module to create a html autogenerated help file for the specified module.
    If file_path is not specified it auto names it and saves it in the current working directory."""
    if re.search('htm',output_format,re.IGNORECASE):
        html_text=pdoc.html(module_name=module,allsubmodules=True)
        if file_path is None:
            file_path=auto_name(module.replace('.','_'),'Help',directory=None,extension='html')
        out_file=open(file_path,'w')
        out_file.write(html_text)
        out_file.close()


def create_examples_page(ipynb_path):
    """Given a jupyter notebook uses nbconvert to output an html file at the specified path."""
    os.system("jupyter nbconvert --to html %s"%ipynb_path)



#-----------------------------------------------------------------------------
# Module Classes

#-----------------------------------------------------------------------------
# Module Scripts
def test_create_help_page(module='pyMeasure.Code.DataHandlers.GeneralModels'):
    "Tests the create help page function, it seems pretty slow"
    os.chdir(TESTS_DIRECTORY)
    create_help_page(module)
def test_create_examples_page(ipynb_path='Development_Stack_Installation_Example_20160130_01.ipynb'):
    """Tests the create_examples_page function, really nb convert on the command line"""
    os.chdir(TESTS_DIRECTORY)
    create_examples_page(ipynb_path)

def autogenerate_api_documentation_script():
    """Autogenerates the api help files. It requires that pdoc is installed and that the pdoc script is in
    the Documentation folder under pyMeasure. If the folder exists it first deletes the folder and then creates a
     new one."""

    os.chdir(DOCUMENTATION_DIRECTORY)
    try:
        shutil.rmtree(os.path.join(DOCUMENTATION_DIRECTORY,"pyMeasure"))
    except:
        print("Could not delete existing API documentation")
        pass
    os.system("python pdoc --html --overwrite pyMeasure")

def create_index_html(top_directory):
    """create_index returns an html page with links to the autogenerated help page for all
    functions and classes in .py files in the directory structure"""
    classes_and_functions=[]
    class_pattern=re.compile('class (?P<name>\w+)\(')
    function_pattern=re.compile('def (?P<name>\w+)\(')
    links_dictionary={}
    link_template="<li><a href='{0}'>{1}</a></li>\n"
    links_string=""
    for directory, dirnames, file_names in os.walk(top_directory):
        clean_directory=directory.split('..\\')[-1].replace("\\","/")
        for file_name in file_names:
            extension=file_name.split(".")[-1]
            if re.match('py',extension,re.IGNORECASE):
                in_file=open(os.path.join(directory,file_name),'r')
                for line in in_file:
                    if re.search(class_pattern,line):
                        reference_file="pyMeasure/"+change_extension(os.path.join(clean_directory,file_name),'m')+".html"
                        reference_id = reference_file.split(".")[0]
                        reference_file="./"+reference_file.replace("\\","/")
                        name=re.search(class_pattern,line).groupdict()['name']
                        reference_id = reference_id.replace("\\", "/")
                        reference_id=reference_id.replace("/", ".")+"."+name
                        reference=reference_file+"#"+reference_id
                        classes_and_functions.append(name)
                        links_string=links_string+ \
                                     link_template.format(reference,
                                                          name)
                        links_dictionary[name]=link_template.format(reference,
                                                          name)
                    elif re.match(function_pattern,line):
                        reference_file="pyMeasure/"+change_extension(os.path.join(clean_directory,file_name),'m')+".html"
                        reference_id = reference_file.split(".")[0]
                        reference_file="./"+reference_file.replace("\\","/")
                        name=re.search(function_pattern,line).groupdict()['name']
                        classes_and_functions.append(name)
                        reference_id = reference_id.replace("\\", "/")
                        reference_id=reference_id.replace("/", ".")+"."+name
                        reference=reference_file+"#"+reference_id
                        links_string=links_string+\
                                     link_template.format(reference,
                                                          name)

                        links_dictionary[name]=link_template.format(reference,
                                                          name)
    #print("{0} is {1}".format('classes_and_functions',classes_and_functions))
    #print("{0} is {1}".format('links_string',links_string))
    links_string="<ol>"+links_string+"</ol>"
    sorted_keys=sorted(links_dictionary.keys(),key=str.lower)
    links_string=""
    for key in sorted_keys:
        links_string=links_string+links_dictionary[key]
    links_string = INDEX_HTML_PREFIX + links_string + INDEX_HTML_POSTFIX
    out_file=open(os.path.join(DOCUMENTATION_DIRECTORY,"Reference_Index.html"),"w")
    out_file.write(links_string)
    out_file.close()



def test_create_index_html(top_directory=PYMEASURE_ROOT):
    create_index_html(top_directory=top_directory)
#-----------------------------------------------------------------------------
# Module Runner
if __name__ == '__main__':
    #test_create_help_page()
    #test_create_help_page('pyMeasure')
    #test_create_help_page('pyMeasure.Code.DataHandlers.NISTModels')
    #test_create_help_page('pyMeasure.Code.DataHandlers')
    #test_create_examples_page()
    #test_create_examples_page(os.path.join(DOCUMENTATION_DIRECTORY,"pyMeasure_Documentation.ipynb"))
    autogenerate_api_documentation_script()
    #test_create_index_html()