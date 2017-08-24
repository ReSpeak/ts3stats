"use strict";

$(function() {
	// Remove borders of focused buttons
	$(".btn, a").mouseup(function() {
		$(this).blur();
	});

	// Set fixed width to diagrams
	$("object").width($("main").width());

	// Smooth scrolling
	$('.sidebar a').click(function() {
		$('html, body').stop().animate({
			scrollTop: $( $(this).attr('href') ).offset().top
		}, 500);
		return true;
	});
	$('.scrollTop a').scrollTop();

	$('[data-toggle="offcanvas"]').click(function () {
		$('.row-offcanvas').toggleClass('active')
	});
});
