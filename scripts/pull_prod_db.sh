psql -c "DROP DATABASE actions_insider;" -U postgres
heroku pg:pull DATABASE_URL postgres://edu@localhost:5432/actions_insider --app buildbudget
