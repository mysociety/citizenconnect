;(function($){
    $(function(){
        var problemsColumns = ['week', 'four_weeks', 'six_months', 'all_time'];
        var reviewsColumns = ['reviews_week', 'reviews_four_weeks', 'reviews_six_months', 'reviews_all_time'];

        var toggleColumnClass = function(selectedClassName, columnClassName) {
            console.log("Toggling column: " + columnClassName + " selected column is: " + selectedClassName);
            if(columnClassName === selectedClassName) {
                $("td." + columnClassName).removeClass("hidden");
            }
            else {
                $("td." + columnClassName).addClass("hidden");
            }
        };

        $("#problems-interval-filters").change(function(e){
            console.log("Change on problems filter");
            var selected = $(this).val();
            var sortLink = "?sort=" + selected;
            // Toggle the right column
            $.each(problemsColumns, function(index, className){
                toggleColumnClass(selected, className);
            });
            // Change the sorting link
            $("th.problems-received > a").attr('href', sortLink);
        });

        $("#reviews-interval-filters").change(function(e){
            var selected = $(this).val();
            var sortLink = "?sort=" + selected;
            $.each(reviewsColumns, function(index, className){
                toggleColumnClass(selected, className);
            });
            // Change the sorting link
            $("th.reviews-received > a").attr('href', sortLink);
        });
    });
})(window.jQuery);