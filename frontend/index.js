eel.expose(myFunc);

function myFunc(availableSlots, totalSlots, suggestedSlot) {
  $("#available").html(availableSlots);
  $("#total").html(totalSlots);
  $("#suggested").html(suggestedSlot);
}
