;(function($){
    $(function(){
        var problemsColumns = ['week', 'four_weeks', 'six_months', 'all_time'];
        var reviewsColumns = ['reviews_week', 'reviews_four_weeks', 'reviews_six_months', 'reviews_all_time'];

        var toggleColumnClass = function(selectedClassName, columnClassName) {
            console.log("Toggling column: " + columnClassName + " selected column is: " + selectedClassName);
            if(columnClassName === selectedClassName) {
                $("." + columnClassName).removeClass("hidden");
            }
            else {
                $("." + columnClassName).addClass("hidden");
            }
        }

        $("#problems-interval-filters").change(function(e){
            console.log("Change on problems filter");
            var selected = $(this).val();
            $.each(problemsColumns, function(index, className){
                toggleColumnClass(selected, className);
            });
        });

        $("#reviews-interval-filters").change(function(e){
            var selected = $(this).val();
            $.each(reviewsColumns, function(index, className){
                toggleColumnClass(selected, className);
            });
        });
    });
})(window.jQuery);