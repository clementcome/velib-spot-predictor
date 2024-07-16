window.dashExtensions = Object.assign({}, window.dashExtensions, {
    default: {
        function0: function(feature, context) {
            console.log(context.hideout);
            console.log(feature);
            const {
                min,
                max,
                colorscale,
                style,
                colorProp
            } = context.hideout;
            const csc = chroma.scale(colorscale).domain([min, max]);
            style.color = csc(feature.properties[colorProp]);
            return style;
        }

    }
});