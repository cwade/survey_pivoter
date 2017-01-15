# Overview

SurveyPivoter is a fairly simple Python 3 script that takes in a survey data file with one row per survey response and outputs a new file that's one row per question response. It's for taking files that come out of Qualtrics (or other survey software) and transforming them for use in Tableau, using [Steve Wexler's recommended methods of survey data visualization](http://www.datarevelations.com/visualizing-survey-data).

It requires installation of the following python libraries (using pip install [library name] or your preferred method):
pandas
PyYAML

*If you want the script to work on SPSS .sav files, you also need to install R and the rpy2 library.* Unfortunately installing rpy2 can be a bit challenging. We'll try to update the documentation with tips once we find them, but in the meantime, if you're just getting started, you may want to stick with csv files at first. 
 
To run the script from the directory where it's located:

```
python3 survey_pivoter.py [config_file]
```

The sample config file included here, config.yml, contains a lot of documentation about all the parameters that need to be specified for the script to work.

Sample data files are also included. If opting for csv files as your input, these can be created by taking an SPSS file and saving it as a csv file twice, once with 'Save value labels where defined instead of data files' checked and once with it unchecked. They can also be created by taking any Qualtrics survey, and downloading the csv file twice, once with 'Use choice text' selected and once with 'Use numeric values' selected. *Note that if you're using Qualtrics csv files, you'll have to delete one of the two header rows in each of your csv files before running the script.*

The script computes a variable called 'count_negative' which is used in Steve Wexler's diverging stacked bar charts. The script assumes that the top half of responses on the numeric scale are positive and the bottom half are negative. If there's an odd number of possible answers, the middle category is counted as half negative and half positive. A shortcoming of the script is that it has no knowledge of the domain of possible answers for a given question, it only knows about the ones that were actually selected by at least one respondent. So if you had a 5 point scale and everyone answered 3, 4, or 5, the script would treat 3 as negative, 4 as half negative, half positive and 5 as positive.

One advantage of using an SPSS file as input is that in SPSS you can encode labels associated with the variable name, in that case the output file will have question_varname set to the name of the question variable (e.g. satisf) and question_text set to the full text of the question. If inputting csv files from Qualtrics, question_variable and question_text will both be set to the variable name. A workaround to this is to use the first header row in the 'values' csv file (deleting the second row) and the second header row in the 'labels' csv file.

This script is still under development and contributions are welcome!

