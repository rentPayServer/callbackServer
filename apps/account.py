
from utils.exceptions import PubErrorCustom
from libs.utils.mytime import UtilTime
from apps.user.models import Users,BalList,UserBal
from libs.utils.log import logger

class AccountBase(object):

    def __init__(self,**kwargs):
        # 是否充值
        self.isPay = kwargs.get('isPay', False)

        # 是否提现
        self.isCashout = kwargs.get('isCashout', False)

        # 是否提现拒绝
        self.isCashoutCanle = kwargs.get('isCashoutCanle', False)

        # 是否提现确认
        self.isCashoutConfirm = kwargs.get('isCashoutConfirm', False)

        # 是否冻结
        self.isStop = kwargs.get('isStop', False)

        # 是否解冻
        self.isStopCanle  = kwargs.get('isStopCanle', False)

        userid = kwargs.get('userid', None)
        if not userid:
            raise PubErrorCustom("用户代码不能为空!")

        self.amount = kwargs.get('amount', None)
        if not self.amount:
            raise PubErrorCustom("交易金额不能为空!")
        else:
            self.amount = float(self.amount)

        self.ordercode = kwargs.get('ordercode', 0)

        paypassid = kwargs.get("paypassid",None)
        if not paypassid:
            raise PubErrorCustom("渠道ID不能为空!")

        try:
            self.user = Users.objects.select_for_update().get(userid=userid)
        except Users.DoesNotExist:
            raise PubErrorCustom("无对应用户信息({})".format(userid))


        try:
            self.userBal = UserBal.objects.select_for_update().get(userid=userid,paypassid=paypassid)
        except UserBal.DoesNotExist:
            self.userBal = UserBal.objects.create(**{
                "userid":userid,
                "paypassid":paypassid,
            })

        logger.info("""动账前: userid:{} amount:{} ordercode:{} totbal:{} bal:{} cashout_bal:{} stop_bal:{}""".format(
            self.user.userid,
            self.user.upd_bal_date,
            self.amount,
            self.ordercode,
            self.user.bal,
            self.userBal.bal,
            self.userBal.cashout_bal,
        ))

        self.today = UtilTime().arrow_to_string(format_v="YYYYMMDD")

        self.RunUpdDate()

    def isUpdDate(self):
        if self.user.upd_bal_date >= self.today:
            return False
        else:
            return True

    def RunUpdDate(self):
        if self.isUpdDate():
            self.user.today_bal = 0.0
            self.user.lastday_bal = self.user.bal

            self.user.today_pay_amount = 0.0
            self.user.lastday_pay_amount = self.user.tot_pay_amount

            self.user.today_cashout_amount = 0.0
            self.user.lastday_cashout_amount = self.user.tot_cashout_amount

            self.user.upd_bal_date = self.today

    def AccountListInsert(self,memo):
        BalList.objects.create(**{
            "userid" : self.user.userid,
            "amount" : self.amount,
            "bal" : self.userBal.bal,
            "paypassid":self.userBal.paypassid,
            "confirm_bal" : float(self.userBal.bal) + float(self.amount),
            "memo" : memo,
            "ordercode": self.ordercode
        })

    def run(self):
        raise PubErrorCustom("function error!")

class AccountPay(AccountBase):

    """
    动账-充值
    """

    def __init__(self,**kwargs):

        kwargs.setdefault("isPay",True)
        super().__init__(**kwargs)

    def run(self):
        logger.info("充值")
        self.AccountListInsert("充值")
        self.user.today_pay_amount = float(self.user.today_pay_amount) + self.amount
        self.user.tot_pay_amount = float(self.user.tot_pay_amount) + self.amount

        self.user.today_bal = float(self.user.today_bal) + self.amount
        self.user.bal = float(self.user.bal) + self.amount
        self.user.save()

        self.userBal.bal = float(self.userBal.bal) + self.amount
        self.userBal.save()

        logger.info("""动账后: userid:{} amount:{} ordercode:{} totbal:{} bal:{} cashout_bal:{} stop_bal:{}""".format(
            self.user.userid,
            self.user.upd_bal_date,
            self.amount,
            self.ordercode,
            self.user.bal,
            self.userBal.bal,
            self.userBal.cashout_bal,
        ))

