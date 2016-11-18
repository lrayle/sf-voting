## includes functions needed for data preparation


def find_matching_sheets(wb, to_match, to_not_match):
	# searches for the right worksheet and return their names as a list.
	# wb:excel workbook with election results
	# to_match: phrase to match
	# to_not_match: phrase to exlude

    sheets =[]
    for s in wb.sheets():
        s_match = re.search(to_match,s.name, flags=re.IGNORECASE)
        not_match = re.search(to_not_match,s.name, flags=re.IGNORECASE)
        if s_match:
            if not not_match:
                #print(s_match.string)
                sheets.append(s_match.string)
    return sheets