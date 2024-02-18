document.addEventListener("DOMContentLoaded", function () {
  const menu = document.querySelector(".menu");
  const menuItems = document.querySelectorAll(".menuItem");
  const hamburger = document.querySelector(".hamburger");
  const closeIcon = document.querySelector(".closeIcon");
  const menuIcon = document.querySelector(".menuIcon");

  function toggleMenu() {
    if (menu.classList.contains("showMenu")) {
      menu.classList.remove("showMenu");
      closeIcon.style.display = "none";
      menuIcon.style.display = "block";
    } else {
      menu.classList.add("showMenu");
      closeIcon.style.display = "block";
      menuIcon.style.display = "none";
    }
  }

  hamburger.addEventListener("click", toggleMenu);


  var typeFilterInput = document.getElementById('typeFilter');
  typeFilterInput.addEventListener('input', filterTable1);

  function filterTable1() {
    var typeFilter = typeFilterInput.value.toLowerCase();
    var tables = document.getElementsByClassName('styled-table');

    for (var j = 0; j < tables.length; j++) {
        var table = tables[j];
        var rows = table.getElementsByTagName('tr');

        for (var i = 1; i < rows.length; i++) {
            var row = rows[i];
            var cells = row.getElementsByTagName('td');
            var content = '';

            for (var k = 0; k < cells.length; k++) {
                content += cells[k].textContent.toLowerCase();
            }

            if (content.includes(typeFilter)) {
                row.style.display = '';
            } else {
                row.style.display = 'none';
            }
        }
      }
    }

    var filterDropdownInput = document.getElementById('filterDropdown');
    filterDropdownInput.addEventListener('input', filterTable);

    function filterTable() {
        var filterDropdown = filterDropdownInput.value.toLowerCase();
        var tables = document.getElementsByClassName('styled-table');

        for (var j = 0; j < tables.length; j++) {
            var table = tables[j];
            var rows = table.getElementsByTagName('tr');

            for (var i = 1; i < rows.length; i++) {
                var row = rows[i];
                var cells = row.getElementsByTagName('td');
                var content = '';

                for (var k = 0; k < cells.length; k++) {
                    content += cells[k].textContent.toLowerCase();
                }

                if (filterDropdown === 'all' || content.includes(filterDropdown)) {
                    row.style.display = '';
                } else {
                    row.style.display = 'none';
                }
            }
        }
    }

    var filterTypeDropdownInput = document.getElementById('filterTypeDropdown');
    filterTypeDropdownInput.addEventListener('input', filterTableTwo);

    function filterTableTwo() {
      var filterTypeDropdown = filterTypeDropdownInput.value.toLowerCase();
      var tables = document.getElementsByClassName('styled-table');

      for (var j = 0; j < tables.length; j++) {
          var table = tables[j];
          var rows = table.getElementsByTagName('tr');

          for (var i = 1; i < rows.length; i++) {
              var row = rows[i];
              var cells = row.getElementsByTagName('td');
              var content = '';

              for (var k = 0; k < cells.length; k++) {
                  content += cells[k].textContent.toLowerCase();
              }

              if (filterTypeDropdown === 'all' || content.includes(filterTypeDropdown)) {
                  row.style.display = '';
              } else {
                  row.style.display = 'none';
              }
          }
      }
  }






      /**
   * Sorts a HTML table.
   *
   * @param {HTMLTableElement} table The table to sort
   * @param {number} column The index of the column to sort
   * @param {boolean} asc Determines if the sorting will be in ascending
   */
  function sortTableByColumn(table, column, asc = false) {
    const dirModifier = asc ? 1 : -1;
    const tBody = table.tBodies[0];
    const rows = Array.from(tBody.querySelectorAll("tr"));

    // Sort each row
    const sortedRows = rows.sort((a, b) => {
      const aColText = a.querySelector(`td:nth-child(${column + 1})`).textContent.trim();
      const bColText = b.querySelector(`td:nth-child(${column + 1})`).textContent.trim();

      return aColText > bColText ? (1 * dirModifier) : (-1 * dirModifier);
    });

    // Remove all existing TRs from the table
    while (tBody.firstChild) {
      tBody.removeChild(tBody.firstChild);
    }

    // Re-add the newly sorted rows
    tBody.append(...sortedRows);

    // Remember how the column is currently sorted
    table.querySelectorAll("th").forEach(th => th.classList.remove("th-sort-asc", "th-sort-desc"));
    table.querySelector(`th:nth-child(${column + 1})`).classList.toggle("th-sort-asc", asc);
    table.querySelector(`th:nth-child(${column + 1})`).classList.toggle("th-sort-desc", !asc);
  }

  document.querySelectorAll(".styled-table th").forEach(headerCell => {
    headerCell.addEventListener("click", () => {
      const tableElement = headerCell.parentElement.parentElement.parentElement;
      const headerIndex = Array.prototype.indexOf.call(headerCell.parentElement.children, headerCell);
      const currentIsAscending = headerCell.classList.contains("th-sort-asc");

      sortTableByColumn(tableElement, headerIndex, !currentIsAscending);
    });
  });

});


// Define the scale array outside the jQuery function
var scale = [['low', 50], ['avg', 56], ['high', 100]];

$(function() {
    $('tr').each(function() {
        // Get the 11th and 12th columns (index 10 and 11)
        var column11 = $(this).find('td:eq(10)');
        var column12 = $(this).find('td:eq(11)');

        // Get scores from the 11th and 12th columns
        var score11 = parseFloat(column11.text());
        var score12 = parseFloat(column12.text());

        // Apply conditional formatting for the 11th column
        for (var i = 0; i < scale.length; i++) {
            if (score11 <= scale[i][1]) {
                column11.addClass(scale[i][0]);
                break; // Break out of the loop once a match is found
            }
        }

        // Apply conditional formatting for the 12th column
        for (var i = 0; i < scale.length; i++) {
            if (score12 <= scale[i][1]) {
                column12.addClass(scale[i][0]);
                break; // Break out of the loop once a match is found
            }
        }
    });
});


