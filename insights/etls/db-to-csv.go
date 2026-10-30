package etl

import (
	"encoding/csv"
	"errors"
	"fmt"
	"log"
	"os"
	"path"
	"strings"

	"github.com/navapbc/its-log/internal/constants"
	"github.com/navapbc/its-log/internal/types"
	"github.com/spf13/viper"
)

func SqliteToCSV(etlP *types.RunEtlParams) error {
	// var sqliteToCsvPrefix string = "sqlite_to_csv"
	// var sqliteToCsvExpectedKeys = []string{
	// 	sqliteToCsvPrefix + "-source", sqliteToCsvPrefix + "-destination",
	// }

	// err := hasExpectedKeys(etlP, sqliteToCsvExpectedKeys)
	// if err != nil {
	// 	return err
	// }

	for _, table := range constants.ITSLOG_TABLES {
		// 1. Execute the query
		rows, err := etlP.Storage.GetDB().Query("SELECT * FROM " + table)
		if err != nil {
			log.Fatal(err)
		}
		defer rows.Close()

		// The CSV file will be based on the app name, the date, and
		// the table name. It will be stored to the same path as the SQLite
		// databases.
		csvFilename := strings.Join(
			[]string{
				etlP.AppId,
				etlP.Storage.YYYYMMDD(),
				table},
			"_") + ".csv"
		csvFullPath := path.Join(viper.GetString("storage.path"), csvFilename)

		file, err := os.Create(csvFullPath)
		if err != nil {
			return fmt.Errorf("could not create CSV: %s", csvFilename)
		}
		defer file.Close()

		writer := csv.NewWriter(file)
		defer writer.Flush()

		columns, err := rows.Columns()
		if err != nil {
			return fmt.Errorf("could not read columns: %s", table)
		}
		if err := writer.Write(columns); err != nil {
			return fmt.Errorf("could not write column names: %s", table)
		}

		for rows.Next() {
			values := make([]interface{}, len(columns))
			valuePointers := make([]interface{}, len(columns))
			for i := range values {
				valuePointers[i] = &values[i]
			}

			if err := rows.Scan(valuePointers...); err != nil {
				return fmt.Errorf("could not read row: %s", table)
			}

			csvRow := make([]string, len(columns))
			for i, val := range values {
				if val == nil {
					csvRow[i] = "" // Handle NULL values
				} else {
					csvRow[i] = fmt.Sprintf("%v", val)
				}
			}
			if err := writer.Write(csvRow); err != nil {
				return fmt.Errorf("could not write row: %s", table)
			}
		}

		if err = rows.Err(); err != nil {
			return errors.New("row handling error at end of process")
		}

		log.Println("exported: " + csvFilename)
	}
	return nil
}
