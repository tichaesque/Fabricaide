// A simple interface for interacting with Adobe Illustrator
//
// Instantiate with
//   new AdobeIllustratorInteraction(executable);
// where path is the full path to to Illustrator exectuable
//
// Supports the following operations:
//  - exportCurrentDocument(filename): Export the currently opened document with the given name
//  - openDocument(filename): Open the given document
//  - swapDocument(filename): Close the currently opened document and open the given one
//  - closeDocument(): Close the currently opened document
//

class AdobeIllustratorInteraction {

  final String OS = platformNames[platform];
  // Full path to Illustrator exectuable
  private final String ILLUSTRATOR_EXE;

  // Script locations
  private final String SAVE_SCRIPT = dataPath("IllustratorScripts/save.jsx");
  private final String SWAP_SCRIPT = dataPath("IllustratorScripts/swap.jsx");
  private final String OPEN_SCRIPT = dataPath("IllustratorScripts/open.jsx");
  private final String CLOSE_SCRIPT = dataPath("IllustratorScripts/close.jsx");
  private final String TMP_SCRIPT = dataPath("IllustratorScripts/tmp.jsx");

  // Create an illustrator interaction tool
  //
  // executable is the full path to the Adobe Illustrator executable
  public AdobeIllustratorInteraction(String executable) {
    ILLUSTRATOR_EXE = executable;
  }

  // Export the currently opened document as an SVG file
  // to the given filename
  public void exportCurrentDocument(String filename) {
    formatScript(SAVE_SCRIPT, "{FABRICAIDE_FILENAME}", filename);
    launchScript();
  }

  // Close the currently opened document then open the given one
  public void swapDocument(String filename) {
    formatScript(SWAP_SCRIPT, "{FABRICAIDE_FILENAME}", filename);
    launchScript();
  }

  // Open the given document
  public void openDocument(String filename) {
    formatScript(OPEN_SCRIPT, "{FABRICAIDE_FILENAME}", filename);
    launchScript();
  }

  // Close the currently opened document
  public void closeDocument() {
    formatScript(CLOSE_SCRIPT, "", "");
    launchScript();
  }

  private void formatScript(String filename, String old, String replacement) {
    replacement = replacement.replace("\\", "\\\\");  // Needed for windows paths
    String[] script = loadStrings(filename);
    for (int i = 0; i < script.length; i++) {
      script[i] = script[i].replace(old, replacement);
    }
    saveStrings(TMP_SCRIPT, script);
  }

  private void launchScript() {
    if (OS.equals("macosx")) {
      exec("open", "-g", TMP_SCRIPT);
    } else {
      launch(new String[]{ ILLUSTRATOR_EXE, TMP_SCRIPT });
    }
  }
}
