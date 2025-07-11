@echo off
REM Backup Django SQLite database and push to GitHub
echo Backing up database...
set DB_FILE=db.sqlite3
set BACKUP_DIR=backup_db
set BACKUP_FILE=%BACKUP_DIR%\db_backup_%DATE:~10,4%-%DATE:~4,2%-%DATE:~7,2%_%TIME:~0,2%%TIME:~3,2%%TIME:~6,2%.sqlite3

REM Create backup directory if it doesn't exist
if not exist %BACKUP_DIR% mkdir %BACKUP_DIR%

REM Copy database file with timestamp
copy %DB_FILE% %BACKUP_FILE%

REM Add and commit backup to git
cd %BACKUP_DIR%
git add .
git commit -m "Automated DB backup %DATE% %TIME%"
git push
cd ..

echo Backup and push complete.
