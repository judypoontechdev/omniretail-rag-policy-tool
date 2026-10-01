async function runCheck() {
  const orderId = document.getElementById("orderId").value.trim();
  const query = document.getElementById("queryInput").value.trim();
  const btn = document.getElementById("submitBtn");
  const output = document.getElementById("outputArea");

  if (!query) {
    alert("Please enter a query.");
    return;
  }

  btn.disabled = true;
  btn.innerText = "Checking...";

  try {
    const res = await fetch("/api/inquire", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        query: query,
        order_id: orderId || null,
      }),
    });

    const data = await res.json();

    output.style.display = "block";
    document.getElementById("outCat").innerText = data.category;
    document.getElementById("outDec").innerText = data.decision;

    const gapElem = document.getElementById("outGapBlock");
    if (data.gap_detected) {
      gapElem.style.display = "block";
      gapElem.innerText = "Policy Gap: " + data.gap_detected;
    } else {
      gapElem.style.display = "none";
    }

    document.getElementById("outAnswer").innerText = data.final_answer;
    document.getElementById("outOrder").innerText = JSON.stringify(
      data.order_details,
      null,
      2,
    );
  } catch (err) {
    alert("Error: " + err.message);
  } finally {
    btn.disabled = false;
    btn.innerText = "Submit";
  }
}
