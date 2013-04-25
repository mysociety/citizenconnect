$(document).ready(function () {
    var defaultProviders = window.CitizenConnect.providers;
    var nhsCentreIcon_1 = L.icon({
        iconUrl: "/static/img/marker1.png",
        iconRetinaUrl: "/static/img/marker1@2x.png",
        iconSize: [16, 16],
        popupAnchor: [-3, -76],
        shadowUrl: "/static/img/shadow.png",
        shadowRetinaUrl: "/static/img/shadow@2x.png",
        shadowSize: [24, 24]
    });
    var nhsCentreIcon_2 = L.icon({
        iconUrl: "/static/img/marker2.png",
        iconRetinaUrl: "/static/img/marker2@2x.png",
        iconSize: [16, 16],
        popupAnchor: [-3, -76],
        shadowUrl: "/static/img/shadow.png",
        shadowRetinaUrl: "/static/img/shadow@2x.png",
        shadowSize: [24, 24]
    });
    var nhsCentreIcon_3 = L.icon({
        iconUrl: "/static/img/marker3.png",
        iconRetinaUrl: "/static/img/marker3@2x.png",
        iconSize: [16, 16],
        popupAnchor: [-3, -76],
        shadowUrl: "/static/img/shadow.png",
        shadowRetinaUrl: "/static/img/shadow@2x.png",
        shadowSize: [24, 24]
    });
    var nhsCentreIcon_4 = L.icon({
        iconUrl: "/static/img/marker4.png",
        iconRetinaUrl: "/static/img/marker4@2x.png",
        iconSize: [16, 16],
        popupAnchor: [-3, -76],
        shadowUrl: "/static/img/shadow.png",
        shadowRetinaUrl: "/static/img/shadow@2x.png",
        shadowSize: [24, 24]
    });
    var nhsCentreIcon_5 = L.icon({
        iconUrl: "/static/img/marker5.png",
        iconRetinaUrl: "/static/img/marker5@2x.png",
        iconSize: [16, 16],
        popupAnchor: [-3, -76],
        shadowUrl: "/static/img/shadow.png",
        shadowRetinaUrl: "/static/img/shadow@2x.png",
        shadowSize: [24, 24]
    });
    var hoverBubbleTemplate = $("script[name=hover-bubble]").text();
    var filterLinkTemplate = $("script[name=filter-link]").text();
    var londonCentre = new L.LatLng(51.505, -0.09);
    var northEastCentre = new L.LatLng(54.95, -1.62);
    var londonZoomLevel = 10;
    var northEastZoomLevel = 10;
    var map = new L.Map('map', {
        minZoom: 10,
        maxZoom: 16
    });
    var oms = new OverlappingMarkerSpiderfier(map);
    var httpstilejson = {
        "attribution": "maps by <a href='http://mapbox.com/about/maps' target='_blank'>MapBox</a>",
        "bounds": [
            -180,
            -85,
            180,
            85
        ],
        "center": [
            -0.10872747650145358,
            51.50436843041894,
            13
        ],
        "data": [
            "https://dnv9my2eseobd.cloudfront.net/v3/jedidiah.map-3lyys17i/markers.geojsonp"
        ],
        "geocoder": "https://dnv9my2eseobd.cloudfront.net/v3/jedidiah.map-3lyys17i/geocode/{query}.jsonp",
        "id": "jedidiah.map-3lyys17i",
        "maxzoom": 17,
        "minzoom": 10,
        "name": "NHS",
        "private": true,
        "scheme": "xyz",
        "tilejson": "2.0.0",
        "tiles": [
            "https://dnv9my2eseobd.cloudfront.net/v3/jedidiah.map-3lyys17i/{z}/{x}/{y}.png"
        ],
        "webpage": "http://tiles.mapbox.com/jedidiah/map/map-3lyys17i"
    };
    // A LayerGroup so that we can handle all the markers in one go
    var markersGroup = new L.LayerGroup();

    // The map zoom controls.
    // Urgh. Leaflet makes it really hard to enable/disable the default
    // zoom control. You have to remove it completely and then add it back
    // in. To further compound things, the first time you try, you can get
    // the default one from map.zoomControl, but any subsequent controls
    // you add are not stored in that property, so we need to keep a
    // reference to the control around all the time.
    var zoomControl = map.zoomControl;

    // Function to lock all the map controls so that you can't
    // interact with it (ie: during reloading of map pins)
    var disableMapControls = function() {
        map.dragging.disable();
        map.touchZoom.disable();
        map.doubleClickZoom.disable();
        map.scrollWheelZoom.disable();
        map.boxZoom.disable();
        map.keyboard.disable();
        // Can't disable the zoomControl, so we have to remove it
        // completely
        map.removeControl(zoomControl);
    };

    // Function to enable all the map controls again
    var enableMapControls = function () {
        map.dragging.enable();
        map.touchZoom.enable();
        map.doubleClickZoom.enable();
        map.scrollWheelZoom.enable();
        map.boxZoom.enable();
        map.keyboard.enable();
        // Add a new zoomControl, see the note above about why this is needed
        zoomControl = new L.Control.Zoom();
        map.addControl(zoomControl);
    };

    // Function to draw an array of providers onto the map
    var drawProviders = function(providers) {
        // current selected issue type, to pass into the popups
        var issueType = '';
        var $categoryFilter = $(".filters form select[name=category]");
        if ($categoryFilter.val() !== '') {
            issueType = $categoryFilter.children("option:selected").text();
        }

        // Wipe anything that's already on the map
        oms.clearMarkers();
        markersGroup.clearLayers();

        providers.forEach(function(nhsCentre){
            var marker, iconClass, content;

            // Determine the icon colour based on issue count (crudely)
            if(nhsCentre.all_time_open <= 0) {
                iconClass = nhsCentreIcon_5;
            }
            else if(nhsCentre.all_time_open <= 3) {
                iconClass = nhsCentreIcon_4;
            }
            else if(nhsCentre.all_time_open <= 6) {
                iconClass = nhsCentreIcon_3;
            }
            else if(nhsCentre.all_time_open <= 12) {
                iconClass = nhsCentreIcon_2;
            }
            else {
                iconClass = nhsCentreIcon_1;
            }

            // Create the marker
            marker = L.marker([nhsCentre.lat, nhsCentre.lon], {
                riseOnHover:true,
                icon: iconClass
            });

            content = _.template(hoverBubbleTemplate, {nhsCentre: nhsCentre, issueType: issueType});

            // Save some custom data in the marker
            marker.nhsCentre = nhsCentre;

            // Set up the events the marker reacts to
            marker.on('mouseover', function(e){
                var hover_bubble = new L.Rrose({
                    offset: new L.Point(2,-4),
                    closeButton: false,
                    autoPan: false
                }).setContent(content)
                .setLatLng(e.target._latlng)
                .openOn(map);
            }).on('mouseout', function(e){
                _.debounce(map.closePopup(), 300);
            });

            // Add the marker to the map
            markersGroup.addLayer(marker);
            // Tell oms about the marker too
            oms.addMarker(marker);
        });
    };

    // Function to bind click handlers for the links which remove filters
    var bindFilterRemoveLinks = function () {
        $(".filter-links a").click(function(e) {
            e.preventDefault();
            var $link = $(e.target);
            var $option = $(".filters form select[name=" + $link.attr('data-field-name') + "] option[value='']");
            // Reset the field in question, then trigger a change and
            // thus ajax submit the form
            $option.prop('selected', 'selected').change();
        });
    };

    // Function to add in some html to show the selected filters
    var showSelectedFilters = function() {
        var $filterLinkContainer = $(".filters .current-filters .filter-links");

        // Remove anything old
        hideSelectedFilters();

        // Create links for each of the filters currently selected
        $(".filters form select").each(function(index, element) {
            $element = $(element);
            if($element.val()) {
                var filter = {
                    displayValue: $element.children('option:selected').text(),
                    fieldName: $element.attr('name')
                };
                var filterLink = _.template(filterLinkTemplate, {filter: filter});
                $filterLinkContainer.append(filterLink);
            }
        });

        // Put new things in
        if($filterLinkContainer.find("a").length > 0) {
            $(".filters .current-filters").show();
        }

        // Make links work
        bindFilterRemoveLinks();
    };

    // Function to hide the selected filters away again
    var hideSelectedFilters = function() {
        $(".filters .current-filters .filter-links").empty();
        $(".filters .current-filters").hide();
    };

    wax.tilejson('https://dnv9my2eseobd.cloudfront.net/v3/jedidiah.map-3lyys17i.jsonp', function(tilejson) {
        map.addLayer(new wax.leaf.connector(httpstilejson)).setView(londonCentre, 1);

        map.setView(londonCentre, londonZoomLevel);

        // OverlappingMarkerSpiderifier controls click events on markers
        // because it needs to know whether or not to spiderify them, so
        // we need to tell it what we want to do when someone clicks an already
        // spiderified link.
        oms.addListener('click', function(marker) {
            window.location=marker.nhsCentre.url;
        });

        // Add the markers
        drawProviders(defaultProviders);
        map.addLayer(markersGroup);
    });

    // Tabs
    $('a#northeast').on('click', function(e) {
        // recenter the map to The north east
        e.preventDefault();
        map.setView(northEastCentre, northEastZoomLevel);
        $('ul.tab-nav a').toggleClass('active');
    });
    $('a#london').on('click', function(e) {
        // recenter the map to london
        e.preventDefault();
        map.setView(londonCentre, londonZoomLevel);
        $('ul.tab-nav a').toggleClass('active');
    });

    // Filters
    // Hide the submit button
    $(".filters input[type=submit]").hide();

    // Add a hidden "format" field to pass via ajax
    $(".filters form").append('<input type="hidden" name="format" value="json" />');

    // Submit the form via ajax on any select change and
    // reload the map pins from the results
    $(".filters form select").change(function(e) {
        var $form = $(".filters form");
        var form_data = $form.serialize();

        // Lock any filter links and make them look locked
        $(".filter-links a").off('click').css({'cursor': 'default'});
        $(".filter-links").css({'opacity': 0.5});

        // Lock the form during the ajax request
        $form.find("select").prop("disabled", "disabled");

        // Lock the map
        disableMapControls();

        // Add a spinner to the map
        $("#map").spin({shadow:true});

        // Try to get new pins
        $.ajax({
            type: 'GET',
            url: $form.attr('action'),
            data: form_data,
            success: function (response) {
                // Display the links which show selected filters
                showSelectedFilters();
                drawProviders(response);
            },
            complete: function (jqXHR, textStatus) {
                // Renable all the things we disabled
                $form.find("select").prop("disabled", false);
                $("#map").spin(false);
                enableMapControls();
                $(".filter-links").css({'opacity': 1});
            },
            error: function (jqXHR, textStatus, errorThrown) {
                // We only have to rebind links if there's an error because
                // if it's successful, they'll get removed and new ones added
                // anyway.
                bindFilterRemoveLinks();
            }
        });
    });
});
