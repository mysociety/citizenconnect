// Javascript to set up drawing of graphs on Friends and Family survey pages
// and make the location selector form auto-submit
(function ($) {

    // Get all the data for a survey contained inside $element
    // Relies on the html structure of $element
    var getSurveyData = function($element) {
        var data = [];
        $element.children('.survey__previous__overall').each(function() {
            data.push([$(this).data('month'), parseInt($(this).data('value'), 10)]);
        });

        return data;
    };

    $(function(){
        // Draw a graph for each set of previous surveys
        $(".survey__previous").each(function(){
            // Get the data from the table
            var dataPoints = getSurveyData($(this));
            // Some fudgy calculations to make sure that the graphs
            // have a little bit of margin on each end, because Flot doesn't
            // have an option for this
            var numGaps = dataPoints.length;
            var xMinWithMargin = -0.2;
            var xMaxWithMargin = (numGaps - 1) + 0.2;
            series = {
                data: dataPoints.reverse(),
                lines: {
                    show: true
                },
                points: {
                    show: true
                },
                color: '#2f9aa8' // $c-aquablue from the sass
            };
            options = {
                yaxis: {
                    max: 100,
                    min: -100
                },
                xaxis: {
                    mode: "categories",
                    min: xMinWithMargin,
                    max: xMaxWithMargin
                },
                grid: {
                    borderWidth: {
                        top: 0,
                        right: 0,
                        bottom: 1,
                        left: 1
                    },
                    borderColor: '#666666'
                }
            };
            // Manually set the height to get a nice graph, if we did this in
            // CSS it would make the element look bad for non-js people
            $(this).css('padding', '0.5em');
            $(this).html('<div class="survey__previous__graph"></div>');
            $(this).children('.survey__previous__graph').css('height', '15em');
            $.plot($(this).children('.survey__previous__graph'), [series], options);
        });

        // Auto-submit the location form when someone chooses a location
        $('#id_location').change(function(){
            $("#location-form").submit();
        });
        $('#location-form .btn').hide();
    });

})(window.jQuery);
