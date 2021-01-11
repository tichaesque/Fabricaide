
function exportFileToSVG(dest) {
  if (app.documents.length > 0) {
    var exportOptions = new ExportOptionsSVG();
    exportOptions.embedRasterImages = true;
    exportOptions.embedAllFonts = false;
    exportOptions.fontSubsetting = SVGFontSubsetting.GLYPHSUSED; 

    var type = ExportType.SVG;
    var fileSpec = new File(dest);

    app.activeDocument.exportFile(fileSpec, type, exportOptions);
  }
}

exportFileToSVG("/Users/tichaseth/Documents/Fabricaide/Fabricaide/src/EasyCutIllustratorUI/data/../../easycutdoc.svg");
