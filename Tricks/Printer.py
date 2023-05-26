def SetCustomPaperSize(paper_name, width_mm, height_mm):
    results = set()
    sdp = System.Drawing.Printing
    print_settings = sdp.PrinterSettings()
    print_document = sdp.PrintDocument()
    print_document.PrinterSettings = print_settings
    for ps in print_settings.PaperSizes:
        # psname = ps.PaperName
        results.update(dir(ps))

    custom_kind = System.Drawing.Printing.PaperKind.Custom
    print_document.DefaultPageSettings.PaperSize.RawKind = int(custom_kind)
    paperSize = sdp.PaperSize(paper_name, width_mm, height_mm)
    print_settings.DefaultPageSettings.PaperSize = paperSize
    print_settings.DefaultPageSettings.PaperSize.PaperName = paper_name
    print_settings.DefaultPageSettings.PaperSize.Width = (int)(width_mm * 100)
    print_settings.DefaultPageSettings.PaperSize.Height = (int)(height_mm * 100)
    print_settings.DefaultPageSettings.Margins = sdp.Margins(0, 0, 0, 0)
    print_settings.DefaultPageSettings.Landscape = True
    return paperSize