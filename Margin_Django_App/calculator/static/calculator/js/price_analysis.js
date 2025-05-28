// Price Analysis page JavaScript
$(document).ready(function() {
    // Get the earliest date from the server
    const earliestDateStr = $('#start_date').attr('min');
    const earliestDate = new Date(earliestDateStr);
    
    // Validate form before submission
    $("#date-range-form").submit(function(event) {
        const startDate = new Date($("#start_date").val());
        const endDate = new Date($("#end_date").val());
        
        // Check if start date is before the earliest available date
        if (startDate < earliestDate) {
            alert("Start date cannot be earlier than " + earliestDateStr + ", which is the earliest date in our dataset.");
            event.preventDefault();
            $("#start_date").val(earliestDateStr);
            return false;
        }
        
        // Check if end date is before start date
        if (endDate < startDate) {
            alert("End date cannot be earlier than start date.");
            event.preventDefault();
            return false;
        }
        
        return true;
    });
});
