// Add an onclick confirmation dialog if user clicks on a delete button/image.
// Cannot do this directly in HTML because of CSP headers :-)

document.addEventListener("DOMContentLoaded", (event) => {
  const dels = document.getElementsByClassName("delete-confirm");
  for (let i = 0; i < dels.length; i++) {
    dels[i].onclick = function() { return confirm('Are you sure you want to delete this fingerprint?'); };
  }
});
