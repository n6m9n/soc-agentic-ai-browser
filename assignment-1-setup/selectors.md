# CSS Selector Identification (Chrome DevTools)

Target page: **https://demoqa.com/automation-practice-form**
Found with the DevTools element inspector (`Cmd+Shift+C`), each selector verified
in the Console with `document.querySelector("<selector>")` returning the element.

Screenshots are in `./screenshots/`.

## 3 form-input selectors
| # | Field | CSS selector | Screenshot |
|---|-------|--------------|------------|
| 1 | Date of Birth | `#dateOfBirthInput` | `Screenshot 2026-06-24 at 3.30.00 AM.png` |
| 2 | Email | `#userEmail` | `Screenshot 2026-06-24 at 3.30.38 AM.png` |
| 3 | Mobile number | `#userNumber` | `Screenshot 2026-06-24 at 3.30.46 AM.png` |

## 2 button selectors
| # | Button | CSS selector | Screenshot |
|---|--------|--------------|------------|
| 1 | Submit | `#submit` | `Screenshot 2026-06-24 at 3.30.15 AM.png` |
| 2 | Calendar next-month nav | `.react-datepicker__navigation` | `Screenshot 2026-06-24 at 3.31.32 AM.png` |

## 1 dropdown selector
| # | Dropdown | CSS selector | Screenshot |
|---|----------|--------------|------------|
| 1 | State (react-select) | `#state` | `Screenshot 2026-06-24 at 3.34.55 AM.png` |

## How to verify in the Console
```js
document.querySelector("#userEmail");                 // an input
document.querySelector("#submit");                    // a button
document.querySelector("#state");                     // the dropdown container
document.querySelector(".react-datepicker__navigation"); // calendar nav button
```
