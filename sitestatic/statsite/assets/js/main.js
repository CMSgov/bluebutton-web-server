$( ".mobile-nav-trigger" ).click(function(event) {
  event.preventDefault();
  $( ".mobile-nav-tray" ).toggleClass( "mobile-nav-tray-expanded" );
});

$( ".mobile-nav-trigger-2" ).click(function(event) {
  $( ".mobile-nav-tray" ).toggleClass( "mobile-nav-tray-expanded" );
});


var lastId,
 topMenu = $("#mainNav"),
 topMenuHeight = topMenu.outerHeight()+1,
 menuItems = topMenu.find("a"),
 scrollItems = menuItems.map(function(){
   var item = $($(this).attr("href"));
    if (item.length) { return item; }
 });


$(window).scroll(function(){
   var fromTop = $(this).scrollTop()+topMenuHeight;

   var cur = scrollItems.map(function(){
     if ($(this).offset().top < fromTop)
       return this;
   });

   cur = cur[cur.length-1];
   var id = cur && cur.length ? cur[0].id : "";

   if (lastId !== id) {
       lastId = id;
       menuItems
         .parent().removeClass("active")
         .end().filter("[href='#"+id+"']").parent().addClass("active");
   }
});
