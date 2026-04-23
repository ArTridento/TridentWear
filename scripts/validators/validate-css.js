const fs = require('fs');
const css = require('css');

try {
  const filePath = './css/styles.css';
  const content = fs.readFileSync(filePath, 'utf-8');
  
  // Try to parse the CSS
  const parsed = css.parse(content);
  
  // Check for parse errors
  if (parsed.stylesheet && parsed.stylesheet.parsingErrors && parsed.stylesheet.parsingErrors.length > 0) {
    console.log('CSS Syntax Errors Found:');
    parsed.stylesheet.parsingErrors.forEach(error => {
      console.log(`  Line ${error.line}: ${error.message}`);
    });
    process.exit(1);
  } else {
    console.log('CSS Validation: PASSED ?');
    console.log(`Successfully parsed CSS file: ${filePath}`);
    console.log(`Total rules: ${parsed.stylesheet.rules.length}`);
    process.exit(0);
  }
} catch (error) {
  console.log('CSS Validation: FAILED');
  console.log(`Error: ${error.message}`);
  process.exit(1);
}
