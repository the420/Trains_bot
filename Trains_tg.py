import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# Scoring configuration
ROUTE_SCORES = {1: 1, 2: 2, 3: 4, 4: 7, 5: 10, 6: 15}
BONUS_POINTS = 5  # For completed mandala routes

class TicketToRideIndiaBot:
    def __init__(self):
        self.players = {}
        self.game_started = False
        
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if self.game_started:
            await update.message.reply_text("Game already in progress! Use /reset to start over")
            return
            
        self.players = {}
        self.game_started = True
        await update.message.reply_text(
            "🚂 Ticket to Ride India Score Tracker!\n\n"
            "Use /addplayer <name> to add players\n"
            "Use /score to record points\n"
            "Use /show to current scores\n"
            "Maximum 4 players"
        )

    async def add_player(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self.game_started:
            await update.message.reply_text("Start with /start first!")
            return
            
        if len(self.players) >= 4:
            await update.message.reply_text("Already have 4 players!")
            return

        if not context.args:
            await update.message.reply_text("Usage: /addplayer <name>")
            return

        name = " ".join(context.args)
        if name in self.players:
            await update.message.reply_text(f"{name} already added!")
            return

        self.players[name] = {
            'routes': [],
            'mandalas': 0,
            'longest_route': 0,
            'destinations': 0,
            'total': 0
        }

        await update.message.reply_text(f"Added player: {name}")

    async def show_scores(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self.game_started:
            await update.message.reply_text("No active game. Start with /start")
            return

        if not self.players:
            await update.message.reply_text("No players added yet!")
            return

        response = "📊 Current Scores:\n\n"
        for player, data in self.players.items():
            response += f"**{player}**\n"
            response += f"Routes: {sum(data['routes'])} pts\n"
            response += f"Mandalas: {data['mandalas']} x {BONUS_POINTS} = {data['mandalas'] * BONUS_POINTS} pts\n"
            response += f"Destinations: {data['destinations']} pts\n"
            response += f"Longest Route: {data['longest_route']} pts\n"
            response += f"Total: {data['total']} pts\n\n"

        await update.message.reply_text(response, parse_mode='Markdown')

    async def score_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self.game_started or not self.players:
            await update.message.reply_text("Add players first!")
            return

        keyboard = []
        for player in self.players:
            keyboard.append([InlineKeyboardButton(player, callback_data=f"score_{player}")])

        await update.message.reply_text(
            "Select player to score:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    async def action_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        
        player = query.data.split("_")[1]
        context.user_data['current_player'] = player

        keyboard = [
            [InlineKeyboardButton("🚂 Add Route", callback_data=f"action_route_{player}")],
            [InlineKeyboardButton("🔄 Mandala Bonus", callback_data=f"action_mandala_{player}")],
            [InlineKeyboardButton("🎯 Destination Tickets", callback_data=f"action_dest_{player}")],
            [InlineKeyboardButton("📏 Longest Route", callback_data=f"action_longest_{player}")],
            [InlineKeyboardButton("❌ Cancel", callback_data="action_cancel")]
        ]

        await query.edit_message_text(
            f"Scoring for {player}:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    async def route_length_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        
        player = query.data.split("_")[2]
        context.user_data['current_player'] = player

        keyboard = []
        for length, points in ROUTE_SCORES.items():
            keyboard.append([InlineKeyboardButton(f"{length} train(s) - {points} pts", 
                            callback_data=f"route_{length}_{player}")])
        keyboard.append([InlineKeyboardButton("❌ Cancel", callback_data="action_cancel")])

        await query.edit_message_text(
            f"Select route length for {player}:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    async def handle_score(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        
        data = query.data
        player = context.user_data.get('current_player')

        if data.startswith('route_'):
            length = int(data.split('_')[1])
            points = ROUTE_SCORES[length]
            self.players[player]['routes'].append(points)
            self.players[player]['total'] += points
            await query.edit_message_text(f"Added {length}-train route ({points} pts) for {player}")

        elif data.startswith('action_mandala_'):
            self.players[player]['mandalas'] += 1
            self.players[player]['total'] += BONUS_POINTS
            await query.edit_message_text(f"Added mandala bonus ({BONUS_POINTS} pts) for {player}")

        elif data.startswith('action_dest_'):
            # Simple implementation - add 10 points per destination
            self.players[player]['destinations'] += 10
            self.players[player]['total'] += 10
            await query.edit_message_text(f"Added destination ticket (10 pts) for {player}")

        elif data.startswith('action_longest_'):
            # Simple implementation - add 10 points for longest route
            self.players[player]['longest_route'] = 10
            self.players[player]['total'] += 10
            await query.edit_message_text(f"Added longest route bonus (10 pts) for {player}")

        elif data == "action_cancel":
            await query.edit_message_text("Scoring cancelled")

    async def reset_game(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        self.players = {}
        self.game_started = False
        await update.message.reply_text("Game reset! Use /start to begin new game")

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        help_text = """
🚂 Ticket to Ride India Score Tracker

Commands:
/start - Start new game
/addplayer <name> - Add player (max 4)
/score - Record points for players
/show - Show current scores
/reset - Reset game
/help - This message

Scoring:
• Routes: 1-6 trains (1-15 points)
• Mandala Bonuses: 5 points each
• Destination Tickets: Varies (fixed 10 here)
• Longest Route: 10 points
        """
        await update.message.reply_text(help_text)

def main():
    # Get token from environment variable
    TOKEN = '8484721953:AAG46x9A6R_VXXkkYeBxXt5IMe9xLhjiMH4'
    if not TOKEN:
        raise ValueError("Please set TELEGRAM_BOT_TOKEN environment variable")

    bot = TicketToRideIndiaBot()
    application = Application.builder().token(TOKEN).build()

    # Add handlers
    application.add_handler(CommandHandler("start", bot.start))
    application.add_handler(CommandHandler("addplayer", bot.add_player))
    application.add_handler(CommandHandler("score", bot.score_menu))
    application.add_handler(CommandHandler("show", bot.show_scores))
    application.add_handler(CommandHandler("reset", bot.reset_game))
    application.add_handler(CommandHandler("help", bot.help_command))
    
    application.add_handler(CallbackQueryHandler(bot.action_menu, pattern="^score_"))
    application.add_handler(CallbackQueryHandler(bot.route_length_menu, pattern="^action_route_"))
    application.add_handler(CallbackQueryHandler(bot.handle_score, pattern="^action_"))
    application.add_handler(CallbackQueryHandler(bot.handle_score, pattern="^route_"))

    print("Bot started...")
    application.run_polling()

if __name__ == '__main__':
    main()
