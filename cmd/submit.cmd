set competition=%1
set file=%2
set comment=%3
kaggle competitions submit -c %competition% -f %file% -m %comment%
@pause