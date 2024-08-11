--class
Blind = Moveable:extend()

--class methods
function Blind:init(X, Y, W, H)
    Moveable.init(self,X, Y, W, H)

    self.children = {}
    self.config = {}
    self.tilt_var = {mx = 0, my = 0, amt = 0}
    self.ambient_tilt = 0.3
    self.chips = 0
    self.zoom = true
    self.states.collide.can = true
    self.colour = copy_table(G.C.BLACK)
    self.dark_colour = darken(self.colour, 0.2)
    self.children.animatedSprite = AnimatedSprite(self.T.x, self.T.y, self.T.w, self.T.h, G.ANIMATION_ATLAS['blind_chips'], G.P_BLINDS.bl_small.pos)
    self.children.animatedSprite.states = self.states
    self.children.animatedSprite.states.visible = false
    self.children.animatedSprite.states.drag.can = true
    self.states.collide.can = true
    self.states.drag.can = true
    self.loc_debuff_lines = {'',''}

    self.shadow_height = 0

    if getmetatable(self) == Blind then 
        table.insert(G.I.CARD, self)
    end
end