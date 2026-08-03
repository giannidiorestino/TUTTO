r <- sqrt(2) / 2
theta <- seq(0, 2 * pi, length.out = 400)
x <- r * cos(theta)
y <- r * sin(theta)

lim <- c(-1.1, 1.1)

png("figures/circle.png", width = 800, height = 800, res = 150)
plot(x, y, type = "l", asp = 1, lwd = 2,
     xlim = lim, ylim = lim, axes = FALSE,
     xlab = "", ylab = "",
     main = expression(paste("Circle of radius ", sqrt(2)/2)))
arrows(lim[1], 0, lim[2], 0, length = 0.1)
arrows(0, lim[1], 0, lim[2], length = 0.1)
text(lim[2], 0, "x", pos = 3)
text(0, lim[2], "y", pos = 4)
abline(a = 1, b = -1, lwd = 2, col = "red")
points(c(0, 1), c(1, 0), pch = 19)
text(0, 1, "(0,1)", pos = 2)
text(1, 0, "(1,0)", pos = 4)
text(lim[2] - 0.05, 1 - (lim[2] - 0.05), "f", pos = 4, col = "red")

# Projective line [1:1/3]: line through the origin with direction ratio 1 : 1/3
m <- (1 / 3) / 1
abline(a = 0, b = m, lwd = 2, col = "blue", lty = 2)
text(lim[2], lim[2] * m, "[1:1/3]", pos = 1, col = "blue")

# p: intersection of the projective line [1:1/3] with f (x + y = 1)
p_x <- 1 / (1 + m)
p_y <- m * p_x
points(p_x, p_y, pch = 19)
text(p_x, p_y, "p", pos = 3)

# rho: intersection of the projective line [1:1/3] with the circle
rho_x <- r / sqrt(1 + m^2)
rho_y <- m * rho_x
points(rho_x, rho_y, pch = 19)
text(rho_x, rho_y, expression(rho), pos = 1)
dev.off()
